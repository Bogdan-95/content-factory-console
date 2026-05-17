# worker/app/comfy_client.py
# HTTP-клиент для общения с ComfyUI API.
# Отвечает за отправку workflow и получение имени сгенерированного файла.

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .settings import settings


class ComfyError(RuntimeError):
    """Ошибка при взаимодействии с ComfyUI API."""

    pass


# submit_prompt — отправить workflow в ComfyUI и получить prompt_id
@retry(
    stop=stop_after_attempt(5),
    # ↑ Максимум 5 попыток при ошибках сети.
    wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
    # ↑ Экспоненциальная задержка между попытками:
    retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
    # ↑ Повторять ТОЛЬКО при сетевых ошибках.
    reraise=True,
)
def submit_prompt(workflow: dict) -> str:
    """POST /prompt → prompt_id. Пятикратный ретрай на сетевые ошибки."""
    with httpx.Client(base_url=settings.comfy_url, timeout=30.0) as c:
        r = c.post("/prompt", json={"prompt": workflow})
        r.raise_for_status()
        data = r.json()
        pid = data.get("prompt_id")
        if not pid:
            raise ComfyError(f"no prompt_id in response: {data}")
        return pid


# fetch_history — получить статус и результат генерации по prompt_id
def fetch_history(prompt_id: str) -> dict | None:
    """GET /history/{prompt_id} → словарь {prompt_id: {...}} или {} пока ещё идёт."""
    with httpx.Client(base_url=settings.comfy_url, timeout=15.0) as c:
        r = c.get(f"/history/{prompt_id}")
        r.raise_for_status()
        return r.json().get(prompt_id)


# extract_filename — вытащить имя файла из ответа /history
def extract_filename(history_entry: dict, save_node_id: str) -> str | None:
    outputs = history_entry.get("outputs") or {}
    node = outputs.get(save_node_id) or {}
    images = node.get("images") or []
    if not images:
        return None
    return images[0].get("filename")
