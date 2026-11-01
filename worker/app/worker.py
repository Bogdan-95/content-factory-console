# главный цикл SKIP LOCKED

import json
import logging
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

from .comfy_client import submit_prompt, fetch_history, extract_filename
from .db import SessionLocal
from .settings import settings

# Логирование — пишем в stdout, Docker подхватывает.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s worker %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("worker")

# Путь к шаблону workflow ComfyUI.
# Path(__file__).parent — папка, где лежит worker.py.
TEMPLATE_PATH = Path(__file__).parent / "workflow_templates" / "base_sdxl_api.json"


def _load_template() -> dict:
    """
    Загрузить workflow-шаблон из JSON-файла.
    """
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


def _apply_params(wf: dict, job: dict) -> dict:
    """Подставляет параметры job в workflow-шаблон. ID узлов берутся из шаблона выше."""
    seed = job["seed"] if job["seed"] >= 0 else random.randint(0, 2**63 - 1)
    wf["3"]["inputs"]["seed"] = seed
    wf["3"]["inputs"]["steps"] = job["steps"]
    wf["3"]["inputs"]["cfg"] = job["cfg"]
    wf["5"]["inputs"]["width"] = job["width"]
    wf["5"]["inputs"]["height"] = job["height"]
    wf["6"]["inputs"]["text"] = job["prompt"]
    wf["7"]["inputs"]["text"] = job["negative"] or ""
    return wf


def pick_one() -> dict | None:
    """Атомарно берём одну queued-job → processing."""
    with SessionLocal() as db:
        row = (
            db.execute(
                text("""
            SELECT id, prompt, negative, width, height, steps, cfg, seed
            FROM jobs
            WHERE status = 'queued'
            ORDER BY created_at, id
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """)
            )
            .mappings()
            .first()
        )
        if not row:
            return None
        job = dict(row)
        # Шаг 2: Сразу пометить как 'processing'.
        db.execute(
            text("UPDATE jobs SET status='processing', started_at=:now WHERE id=:id"),
            {"id": job["id"], "now": datetime.now(timezone.utc)},
        )
        db.commit()
        return job


def mark_done(job_id: int, prompt_id: str, filename: str) -> None:
    """
    Пометить задачу как выполненную и сохранить имя файла.

    Две операции в одной транзакции:
        1. INSERT в job_results — сохраняем filename.
        2. UPDATE jobs — статус 'done', фиксируем prompt_id и время завершения.
    """
    with SessionLocal() as db:
        db.execute(
            text("INSERT INTO job_results (job_id, filename) VALUES (:id, :f)"),
            {"id": job_id, "f": filename},
        )
        db.execute(
            text(
                "UPDATE jobs SET status='done', comfy_prompt_id=:pid, finished_at=:now WHERE id=:id"
            ),
            {"id": job_id, "pid": prompt_id, "now": datetime.now(timezone.utc)},
        )
        db.commit()


def mark_failed(job_id: int, err: str) -> None:
    """
    Пометить задачу как проваленную с текстом ошибки.

    err[:2000] — обрезаем сообщение до 2000 символов
    (защита от гигантских traceback'ов в БД).
    """
    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE jobs SET status='failed', error=:e, finished_at=:now WHERE id=:id"
            ),
            {"id": job_id, "e": err[:2000], "now": datetime.now(timezone.utc)},
        )
        db.commit()


def process(job: dict) -> None:
    """
    Полный цикл обработки одной задачи:
    1. Загрузить шаблон workflow.
    2. Подставить параметры задачи.
    3. Отправить в ComfyUI → получить prompt_id.
    4. Опрашивать /history до получения filename или таймаута.
    5. Сохранить результат в БД.
    """
    wf = _apply_params(_load_template(), job)
    prompt_id = submit_prompt(wf)
    log.info("job %s submitted to ComfyUI as %s", job["id"], prompt_id)

    deadline = time.time() + settings.worker_comfy_timeout_sec
    while time.time() < deadline:
        entry = fetch_history(prompt_id)
        if entry:
            filename = extract_filename(entry, settings.comfy_save_node_id)
            if filename:
                mark_done(job["id"], prompt_id, filename)
                log.info("job %s done: %s", job["id"], filename)
                return
        time.sleep(settings.worker_comfy_poll_interval_sec)

    raise TimeoutError(
        f"ComfyUI did not finish prompt {prompt_id} in {settings.worker_comfy_timeout_sec}s"
    )


# ГЛАВНЫЙ ЦИКЛ
def main() -> None:
    """
    Бесконечный цикл Worker'а:
    1. Взять задачу из очереди (pick_one).
    2. Если нет задач — поспать.
    3. Обработать задачу (process).
    4. При ошибке — пометить failed и продолжить.
    """
    log.info("worker started, polling every %.1fs", settings.worker_poll_interval_sec)
    while True:
        try:
            job = pick_one()
            if not job:
                time.sleep(settings.worker_poll_interval_sec)
                continue
            try:
                process(job)
            except Exception as exc:  # noqa: BLE001
                log.exception("job %s failed", job["id"])
                mark_failed(job["id"], repr(exc))
        except Exception:  # noqa: BLE001
            log.exception("worker loop error")
            time.sleep(settings.worker_poll_interval_sec)


# Точка входа
if __name__ == "__main__":
    main()
