# 🧑‍💻 DEVELOPER.md — Руководство разработчика

## 1. Назначение

«Пульт контент‑завода» — backend для постановки в очередь и исполнения задач генерации изображений через ComfyUI.  
FastAPI принимает запросы, пишет job в Postgres, worker через `FOR UPDATE SKIP LOCKED` вытаскивает их и гоняет в ComfyUI по HTTP.

## 2. Архитектура (кратко)

Client → FastAPI (api) → Postgres (jobs)
↑
Worker ── POST /prompt ──→ ComfyUI ── PNG ──→ output volume
↓
Postgres (jobs SET done) + job_results
Client ← FastAPI GET /files/{filename}

**Жизненный цикл job:**
1. `POST /generate` → валидация Pydantic → `INSERT INTO jobs (status='queued')` → ответ 202 `job_id`.
2. Worker выполняет `SELECT … FOR UPDATE SKIP LOCKED LIMIT 1` → забирает одну queued‑job атомарно, переводит в `processing`.
3. Worker подставляет параметры задачи в шаблон `base_sdxl_api.json` и отправляет `POST http://host.docker.internal:8188/prompt`.
4. ComfyUI возвращает `prompt_id`. Worker опрашивает `GET /history/{prompt_id}` каждые 2 секунды.
5. Когда в ответе появляется `outputs.<save_node>.images[0].filename` → `INSERT INTO job_results` + `UPDATE jobs SET status='done'`.
6. Клиент запрашивает `GET /jobs/{id}/result` → получает имя файла → `GET /files/{filename}` → API отдаёт PNG из read‑only volume.

## 3. Ключевые инварианты

- Workflow JSON для ComfyUI должен быть в **API‑формате** (кнопка «Save (API Format)» в интерфейсе ComfyUI), а не в UI‑формате.
- В `.env` параметр `COMFY_SAVE_NODE_ID` обязан указывать на ID узла `SaveImage` из используемого шаблона.
- Все запросы к БД проходят через `SessionLocal`; для надёжности включён `pool_pre_ping=True`.
- Функция `pick_one` атомарна: `FOR UPDATE SKIP LOCKED LIMIT 1` и `UPDATE ... WHERE id=:id` выполняются в одной транзакции.
- Контейнер API монтирует `/comfy_output` **read‑only**. Писать в output может только ComfyUI (и worker при необходимости).

## 4. Локальный dev без Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r api/requirements.txt -r worker/requirements.txt pytest ruff
docker run -d --name pg -p 5432:5432 \
  -e POSTGRES_USER=app -e POSTGRES_PASSWORD=app -e POSTGRES_DB=content_factory \
  postgres:16-alpine
docker exec -i pg psql -U app -d content_factory < migrations/001_init.sql
export DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/content_factory
export COMFY_URL=http://localhost:8188
export COMFY_OUTPUT_DIR=/path/to/ComfyUI/output

# Терминал 1
uvicorn api.app.main:app --reload

# Терминал 2
python -m worker.app.worker
```

## 5. Запуск тестов

```bash
export TEST_DATABASE_URL=postgresql+psycopg://test:test@localhost:5432/test
pytest tests/ -v
```

### Что покрыто тестами:

```text
test_health.py — эндпоинт /health возвращает 200.

test_generate.py — успешное создание задачи + проверка валидации (пустой промпт → 422).

test_files_security.py — 5 параметризованных кейсов на защиту от path traversal (.., ..%2F, поддиректории, скрытые файлы, пустая строка).

test_worker_pick.py — интеграционный тест: одна сессия блокирует первую job через FOR UPDATE, pick_one() обязан взять следующую (проверка SKIP LOCKED).
```

## 6. Стиль кода

- `ruff check` + `ruff format`.
- Type hints — везде, где осмысленно.
- Функция ≤ 40 строк.
- Никаких голых `except:` — всегда `except Exception:` с логированием.

## 7. Как добавить новый параметр генерации (пример — `sampler`)

1. `migrations/00N_add_sampler.sql` — `ALTER TABLE jobs ADD COLUMN sampler TEXT NOT NULL DEFAULT 'euler';`
2. `api/app/schemas.py::GenerateIn` — `sampler: str = Field("euler", pattern="^[a-z_]+$")`.
3. `api/app/services/jobs.py::create_job` — включить в `INSERT`.
4. `worker/app/worker.py::_apply_params` — `wf["3"]["inputs"]["sampler_name"] = job["sampler"]`.
5. `tests/test_generate.py` — тест валидации и прохождения по пайплайну.

## 8. Как добавить новый workflow‑шаблон

1. В ComfyUI нарисовать граф, сохранить в API‑формате.
2. Положить в `worker/app/workflow_templates/<name>.json`.
3. Расширить `GenerateIn` полем `template: Literal["sdxl", "sd15"]`.
4. В `worker.py::_load_template` подгружать по имени.

## 9. Миграции БД

Для MVP — plain SQL в `migrations/NNN_*.sql`. Для прода — Alembic:

```bash
pip install alembic
alembic init migrations_alembic
# alembic.ini → sqlalchemy.url = ${DATABASE_URL}
alembic revision -m "init"
alembic upgrade head
```

## 10. Релизная политика

- `main` — всегда зелёный, CI обязателен.
- Ветки `release-1`, `release-2` — снэпшоты конкретных релизов.
- Теги `v1.0.0`, `v2.0.0` — неизменяемые точки отката.
- SemVer: major — breaking, minor — фичи, patch — багфиксы.

## 11. Лицензия

Проект распространяется под лицензией Apache License 2.0.