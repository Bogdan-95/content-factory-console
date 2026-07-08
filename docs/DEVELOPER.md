# 🧑‍💻 DEVELOPER.md — Руководство разработчика (Release 2)

## 1. Назначение

«Пульт контент‑завода» — backend для постановки в очередь и исполнения задач генерации изображений через ComfyUI.  
FastAPI принимает запросы, пишет job в Postgres, worker через `FOR UPDATE SKIP LOCKED` вытаскивает их и гоняет в ComfyUI по HTTP.
**Начиная с версии 2.0.0 ComfyUI запускается как Docker‑сервис**, модели скачиваются автоматически.

---

## 2. Архитектура (кратко)

Client → FastAPI (api) → Postgres (jobs)
↑
Worker ←───────────────────┘ (SKIP LOCKED)
│
└── POST /prompt → ComfyUI (сервис comfyui) → PNG в named volume comfy_output
↓
Client ← FastAPI GET /files/{filename} ← read‑only volume

**Жизненный цикл job:**
1. `POST /generate` → валидация Pydantic → `INSERT INTO jobs (status='queued')` → ответ 202 `job_id`.
2. Worker выполняет `SELECT … FOR UPDATE SKIP LOCKED LIMIT 1` → забирает одну queued‑job атомарно, переводит в `processing`.
3. Worker подставляет параметры задачи в шаблон `base_sdxl_api.json` и отправляет `POST http://host.docker.internal:8188/prompt`.
4. ComfyUI возвращает `prompt_id`. Worker опрашивает `GET /history/{prompt_id}` каждые 2 секунды.
5. Когда в ответе появляется `outputs.<save_node>.images[0].filename` → `INSERT INTO job_results` + `UPDATE jobs SET status='done'`.
6. Клиент запрашивает `GET /jobs/{id}/result` → получает имя файла → `GET /files/{filename}` → API отдаёт PNG из read‑only volume.

**Обязательные сервисы Docker Compose:**
- `postgres` – база данных (том `pg_data`).
- `preflight` – одноразовый сервис, скачивает модели в `comfy_models` (перед стартом ComfyUI).
- `comfyui` – GPU‑ускоренный ComfyUI (тома `comfy_models`, `comfy_output`).
- `api` – FastAPI (read‑only доступ к `comfy_output`).
- `worker` – обработчик очереди.

## 3. Ключевые инварианты

- Workflow JSON для ComfyUI должен быть в **API‑формате** («Save (API Format)» в интерфейсе ComfyUI).
- `COMFY_SAVE_NODE_ID` в `.env` указывает на ID узла `SaveImage` из шаблона.
- Все запросы к БД — через `SessionLocal`; `pool_pre_ping=True`.
- Функция `pick_one` атомарна: `FOR UPDATE SKIP LOCKED LIMIT 1` и `UPDATE` в одной транзакции.
- API монтирует `comfy_output` **read‑only**.
- **Все продуктовые эндпоинты** требуют заголовок `X-API-Key`, кроме `/health`.
- Rate‑limiter (`slowapi`) включён на `/generate`.

## 4. Локальная разработка 

### Рекомендуемый способ (Docker Compose)

```bash
cp .env.example .env   # + поправить пароль/ключ
docker compose up --build
```

Остановка без потери данных:

```bash
docker compose down
```

Для быстрой **пересборки** только api/worker:

```bash
docker compose up -d --build api worker
```

### Альтернатива — отдельные компоненты без Docker (для отладки)

```bash
# 1. Запустите ComfyUI (на хосте или в Docker с портом 8188)
# 2. Поднимите Postgres:
docker run -d --name pg -p 5432:5432 \
  -e POSTGRES_USER=app -e POSTGRES_PASSWORD=app -e POSTGRES_DB=content_factory \
  postgres:16-alpine

# 3. Примените миграции Alembic (из корня проекта)
export DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/content_factory
alembic upgrade head


# 4. Установите остальные переменные и запустите API/Worker
export COMFY_URL=http://localhost:8188
export COMFY_OUTPUT_DIR=/tmp/comfy_output
export API_KEY=dev-local-key-change-me

# Запустите API и Worker в разных терминалах:

```bash
uvicorn api.app.main:app --reload

python -m worker.app.worker
```

## 5. Запуск тестов

```bash
export TEST_DATABASE_URL=postgresql+psycopg://test:test@localhost:5432/test
pytest tests/ -v
```

### Что покрыто тестами:

- test_health.py — /health возвращает 200.

- test_generate.py — создание задачи + валидация.

- test_files_security.py — защита от path traversal.

- test_worker_pick.py — проверка SKIP LOCKED.

## 6. Стиль кода

- `ruff check` + `ruff format`.
- Type hints — везде, где осмысленно.
- Функция ≤ 40 строк.
- Никаких голых `except:` — всегда `except Exception:` с логированием.

## 7. Как добавить новый параметр генерации

1. Alembic - миграции `migrations_alembic`

```bash
alembic revision -m "add_new_param"
```

2. Поле в `api/app/schemas.py::GenerateIn.`

3. Вставка в `api/app/services/jobs.py::create_job.`

4. Применение в `worker/app/worker.py::_apply_params.`

5. Тест в `tests/test_generate.py.`

## 8. Как добавить новый workflow‑шаблон

1. Сохранить граф в API‑формате в worker/app/workflow_templates/.

2. Расширить GenerateIn полем template.

3. В worker.py::_load_template выбирать по имени.

## 9. Миграции БД

#### 1. Создание миграций

```bash
alembic revision -m "описание"
# редактируете файл в migrations_alembic/versions/
alembic upgrade head   # применить локально
```

Вызов **Alembic:**

```bash
pip install alembic
alembic init migrations_alembic
# alembic.ini → sqlalchemy.url = ${DATABASE_URL}
alembic revision -m "init"
alembic upgrade head
```

## 10. Безопасность

- API‑ключ обязателен на `/generate, /jobs, /files` (роутеры используют dependencies=[Depends(require_api_key)]).

- Rate‑limit (slowapi) на POST `/generate` — значение RATE_LIMIT_PER_MIN из .env.

- CORS разрешает только источники из `ALLOWED_ORIGINS`.

- Read‑only volume comfy_output.

- Не‑root пользователь в контейнерах.

- Сгенерируйте сильный ключ: `openssl rand -hex 32`

- Пароль Postgres должен быть уникальным и не совпадать с дефолтным.

## 11. Релизная политика

- `main` — всегда зелёный, CI обязателен.

- Ветки `release-1`, `release-2` — снэпшоты релизов.

Теги `v1.0.0`, `v2.0.0` — неизменяемые точки отката.

SemVer: major — breaking, minor — фичи, patch — багфиксы.

## 12. Лицензия

### Apache License 2.0.

