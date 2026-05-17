<div align="center">

# 🏭 Content Factory Console

</div>
<p align="center">
  <strong>Backend‑обвязка над ComfyUI: REST API + очередь задач в PostgreSQL + асинхронный worker.<br>Генерация изображений Stable Diffusion XL одной командой <code>docker compose up</code>.</strong>
</p>
<div align="center">
---


[![Release v1.0.0](https://img.shields.io/badge/release-v1.0.0-blue)](./CHANGELOG.md)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-latest-orange?logo=comfyui&logoColor=white)](https://github.com/comfyanonymous/ComfyUI)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen?style=flat-square&logo=pytest&logoColor=white)](./tests)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue?style=flat-square&logo=apache&logoColor=white)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker_Compose-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![httpx](https://img.shields.io/badge/httpx-0.27-009688?style=flat-square)](https://www.python-httpx.org/)
[![Ruff](https://img.shields.io/badge/code_style-ruff-D7FF64?style=flat-square&logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)

---

[🚀 Быстрый старт](#-быстрый-старт) ·
[📡 API](#-api) ·
[🏗 Архитектура](#-архитектура) ·
[📦 Релизы и Roadmap](#-релизы-и-roadmap) ·
[📋 CHANGELOG](./CHANGELOG.md) ·
[🔒 Security](./SECURITY.md)

</div>

---

> 📸 **Скриншот рабочего пайплайна** (Swagger UI + сгенерированная картинка) — добавляется в `docs/screenshots/` после первого smoke-теста.

---

## 🎯 Что это и зачем

**Проблема:** ComfyUI — мощный UI-конструктор поверх Stable Diffusion XL, но это именно UI: один человек, одна вкладка, нет очереди, нет API, нет масштабирования.

**Решение:** «Пульт контент-завода» превращает ComfyUI в production-ready API-сервис:

|     | Возможность                                                          |
| --- | -------------------------------------------------------------------- |
| ✅   | Принимает HTTP-запросы на генерацию                                  |
| ✅   | Складывает их в очередь (PostgreSQL + `FOR UPDATE SKIP LOCKED`)      |
| ✅   | Worker асинхронно гоняет ComfyUI и сохраняет результаты              |
| ✅   | Один `docker compose up --build` — и у тебя рабочий генератор        |
| ✅   | Горизонтальное масштабирование: `docker compose up --scale worker=N` |
| ✅   | **Без Redis / Celery / RabbitMQ** — только Postgres                  |

---

## 📑 Содержание

- [🏭 Content Factory Console](#-content-factory-console)
  - [](#)
  - [🎯 Что это и зачем](#-что-это-и-зачем)
  - [📑 Содержание](#-содержание)
  - [✨ Возможности](#-возможности)
  - [🏗 Архитектура](#-архитектура)
    - [Жизненный цикл Job](#жизненный-цикл-job)
  - [🔧 Стек](#-стек)
  - [📋 Требования](#-требования)
    - [Минимальные](#минимальные)
    - [Проверено на](#проверено-на)
  - [🚀 Быстрый старт](#-быстрый-старт)
    - [1. Клонировать](#1-клонировать)
    - [2. Настроить окружение](#2-настроить-окружение)
    - [3. Запустить ComfyUI на хосте](#3-запустить-comfyui-на-хосте)
    - [4. Поднять пульт](#4-поднять-пульт)
    - [5. Проверить](#5-проверить)
  - [⚙️ Конфигурация](#️-конфигурация)
  - [📡 API](#-api)
    - [`GET /health`](#get-health)
    - [`POST /generate`](#post-generate)
    - [`GET /jobs/{id}`](#get-jobsid)
    - [`GET /jobs/{id}/result`](#get-jobsidresult)
    - [`GET /files/{filename}`](#get-filesfilename)
  - [🗂 Структура проекта](#-структура-проекта)
  - [🧑‍💻 Разработка](#-разработка)
    - [Локальный dev без Docker](#локальный-dev-без-docker)
    - [Качество кода](#качество-кода)
    - [Добавить новый параметр генерации](#добавить-новый-параметр-генерации)
  - [🧪 Тесты и CI](#-тесты-и-ci)
    - [Запустить локально](#запустить-локально)
    - [Покрытие тестов](#покрытие-тестов)
    - [GitHub Actions](#github-actions)
  - [🔒 Безопасность](#-безопасность)
    - [Что уже включено в MVP](#что-уже-включено-в-mvp)
  - [🩺 Траблшутинг](#-траблшутинг)
  - [📦 Релизы и Roadmap](#-релизы-и-roadmap)
  - [📚 Документация](#-документация)
  - [🤝 Contributing](#-contributing)
  - [🛡️ Сообщить об уязвимости](#️-сообщить-об-уязвимости)
  - [📜 Лицензия](#-лицензия)
  - [👤 Автор](#-автор)

---

## ✨ Возможности

- 🚀 **REST API на FastAPI:** `POST /generate`, `GET /jobs/{id}`, `GET /jobs/{id}/result`, `GET /files/{name}`, `GET /health`. Swagger UI на `/docs`.
- 🗄️ **Очередь в Postgres** через `SELECT … FOR UPDATE SKIP LOCKED` — без Redis/Celery/RabbitMQ. Горизонтальное масштабирование одной командой `docker compose up --scale worker=N`.
- ⚙️ **Worker на httpx + tenacity:** подставляет промпт в API-формат workflow, шлёт в ComfyUI, опрашивает `/history/{prompt_id}`, сохраняет filename. Экспоненциальные ретраи на сетевые ошибки.
- 🐳 **Docker Compose:** Postgres 16 + API + Worker — одной командой, с healthcheck для БД и `depends_on: condition: service_healthy`.
- ✅ **Тесты + CI:** pytest с реальным Postgres в GitHub Actions services + ruff lint/format + `docker compose build`.
- 🔒 **Безопасность из коробки:** защита от path traversal, read-only монт `output/`, non-root user в контейнерах, изолированная Docker-сеть, валидация входа Pydantic v2, опциональный API-key и rate-limit.
- 📘 **Документация на трёх уровнях:** README (продажа), `docs/DEVELOPER.md` (внутрь), `docs/USER_GUIDE.md` (наружу).

---

## 🏗 Архитектура

```mermaid
graph LR
    A["🖥️ Client"] -->|"POST /generate"| B["⚡ FastAPI :8000"]
    B -->|"INSERT jobs"| C[("🗄️ PostgreSQL")]
    D["⚙️ Worker"] -->|"FOR UPDATE SKIP LOCKED"| C
    D -->|"POST /prompt"| E["🎨 ComfyUI :8188 (host)"]
    E -->|"GET /history/{id}"| D
    D -->|"UPDATE done"| C
    A -->|"GET /jobs/{id}"| B
    A -->|"GET /files/{name}"| B
    B -->|"read PNG :ro"| F["📁 ComfyUI output/"]
    E -->|"save PNG"| F
```

### Жизненный цикл Job

```
POST /generate
     │
     ▼
Pydantic-валидация
     │
     ▼
INSERT INTO jobs (status='queued')  ──►  202 { job_id }
     │
     ▼
Worker: SELECT … FOR UPDATE SKIP LOCKED LIMIT 1
     │
     ▼
status = 'processing'
     │
     ▼
POST http://host.docker.internal:8188/prompt  (подставлен workflow)
     │
     ▼
Polling GET /history/{prompt_id}  каждые 2 сек
     │
     ▼
outputs.<save_node>.images[0].filename получен
     │
     ▼
INSERT INTO job_results  +  UPDATE jobs SET status='done'
     │
     ▼
GET /jobs/{id}/result  ──►  { filename }
GET /files/{filename}  ──►  PNG (read-only volume)
```

---

## 🔧 Стек

| Слой              | Технологии                                         |
| ----------------- | -------------------------------------------------- |
| **Язык**          | Python 3.12                                        |
| **Web**           | FastAPI 0.115, Pydantic v2, pydantic-settings 2.6  |
| **БД**            | PostgreSQL 16, SQLAlchemy 2.0, psycopg v3          |
| **Очередь**       | Postgres `FOR UPDATE SKIP LOCKED` (zero-broker)    |
| **HTTP-клиент**   | httpx 0.27 + tenacity 9 (экспоненциальный backoff) |
| **Тесты**         | pytest, FastAPI TestClient, реальный Postgres в CI |
| **Качество**      | ruff (lint + format), type hints везде             |
| **Контейнеры**    | Docker, docker-compose                             |
| **CI**            | GitHub Actions: lint → test → build                |
| **AI-интеграция** | ComfyUI HTTP API + SDXL Base 1.0                   |

---

## 📋 Требования

### Минимальные

| Компонент   | Требование                                                                                                  |
| ----------- | ----------------------------------------------------------------------------------------------------------- |
| **ОС**      | Ubuntu 22.04+ / Windows 11 + WSL2 / macOS ⚠️                                                                 |
| **Docker**  | Engine 24+ + docker-compose plugin                                                                          |
| **RAM**     | 16 ГБ                                                                                                       |
| **Диск**    | 50 ГБ свободного места                                                                                      |
| **GPU**     | NVIDIA ≥ 8 ГБ VRAM (нужен ComfyUI; пульт работает и без GPU)                                                |
| **ComfyUI** | Установленный и запущенный ([github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)) |

> ⚠️ **macOS:** нет nvidia-passthrough в Docker. Ставь ComfyUI нативно или на удалённой машине.

### Проверено на

```
Ubuntu 22.04 / WSL2 + RTX 5060 Laptop 8 GB VRAM, PyTorch 2.12.0+cu128
```

---

## 🚀 Быстрый старт

### 1. Клонировать

```bash
git clone git@github.com:Bogdan-95/content-factory-console.git
cd content-factory-console
```

### 2. Настроить окружение

```bash
cp .env.example .env
```

Отредактируй `.env`:

```bash
POSTGRES_PASSWORD=<любой непустой>
COMFY_OUTPUT_HOST=/full/path/to/ComfyUI/output
API_KEY=<любой в dev>  # для прода см. docs/DEVELOPER.md §10.2
```

### 3. Запустить ComfyUI на хосте

> ⚠️ **Важно:** ComfyUI должен слушать `0.0.0.0`, иначе контейнеры не достучатся.

```bash
cd /path/to/ComfyUI
python main.py --listen 0.0.0.0 --port 8188

# Проверка:
curl -sI http://localhost:8188/ | head -1
# HTTP/1.1 200 OK
```

### 4. Поднять пульт

```bash
docker compose up --build
# postgres → healthy → api → worker
# Логи смотри в реальном времени
```

### 5. Проверить

```bash
# Health check
curl http://localhost:8000/health
# {"ok": true}

# Создать job
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"a beautiful sunset, masterpiece, 8k","steps":20}'
# {"job_id": 1, "status": "queued"}

# Опрос статуса (queued → processing → done)
watch -n 2 'curl -s http://localhost:8000/jobs/1'

# Получить имя файла
curl http://localhost:8000/jobs/1/result

# Скачать PNG
curl -O http://localhost:8000/files/ComfyUI_00001_.png
```

> 💡 Или всё одной командой через smoke-скрипт: `./scripts/smoke.sh`

---

## ⚙️ Конфигурация

Все настройки — через `.env`. Полный шаблон — в `.env.example`.

| Переменная                       | По умолчанию                                               | Назначение                                                                        |
| -------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `POSTGRES_PASSWORD`              | —                                                          | Пароль БД (**обязательно**). В проде: `openssl rand -base64 32`                   |
| `DATABASE_URL`                   | `postgresql+psycopg://app:…@postgres:5432/content_factory` | URL для SQLAlchemy. Драйвер — psycopg v3                                          |
| `COMFY_URL`                      | `http://host.docker.internal:8188`                         | URL ComfyUI. R1: на хосте; R2: `http://comfyui:8188`                              |
| `COMFY_OUTPUT_HOST`              | —                                                          | Путь к `ComfyUI/output` на хосте. Монтируется в API как `/comfy_output:ro`        |
| `COMFY_SAVE_NODE_ID`             | `9`                                                        | ID узла `SaveImage` в `base_sdxl_api.json`. При смене шаблона — синхронизируй     |
| `API_KEY`                        | `dev-local-key-change-me`                                  | API-ключ. В проде: `openssl rand -hex 32` + подключить `Depends(require_api_key)` |
| `RATE_LIMIT_PER_MIN`             | `30`                                                       | Лимит на `/generate` (slowapi). Ключ — IP клиента                                 |
| `ALLOWED_ORIGINS`                | `http://localhost:3000`                                    | CORS allowlist (через запятую). **Не `*`**                                        |
| `WORKER_POLL_INTERVAL_SEC`       | `2`                                                        | Период опроса очереди worker'ом                                                   |
| `WORKER_COMFY_POLL_INTERVAL_SEC` | `2`                                                        | Период опроса `/history/{id}` в ComfyUI                                           |
| `WORKER_COMFY_TIMEOUT_SEC`       | `600`                                                      | Таймаут одной job. После истечения — `failed`                                     |

---

## 📡 API

> 📖 Полный Swagger UI: `http://localhost:8000/docs`  
> 📖 ReDoc: `http://localhost:8000/redoc`

---

### `GET /health`

Liveness-пинг для k8s / uptime-мониторинга.

```
200 OK
{"ok": true}
```

---

### `POST /generate`

Создаёт job на генерацию. Возвращает `job_id` **сразу**, не дожидаясь ComfyUI.

**Request body:**

```json
{
  "prompt": "a cozy cabin in the snowy forest, volumetric light",
  "negative": "low quality, blurry",
  "width": 1024,
  "height": 1024,
  "steps": 25,
  "cfg": 7.5,
  "seed": -1
}
```

**Поля запроса:**

| Поле       | Тип    | Диапазон        | По умолчанию     |
| ---------- | ------ | --------------- | ---------------- |
| `prompt`   | string | 1…2000 символов | **обязательно**  |
| `negative` | string | 0…2000 символов | `""`             |
| `width`    | int    | 256…2048        | `1024`           |
| `height`   | int    | 256…2048        | `1024`           |
| `steps`    | int    | 1…80            | `20`             |
| `cfg`      | float  | 0…30            | `7.0`            |
| `seed`     | int    | ≥ −1            | `-1` (случайный) |

**Ответ `202`:**

```json
{"job_id": 7, "status": "queued"}
```

**Ошибки:** `422` — Pydantic-валидация · `429` — rate-limit · `403` — bad API key

---

### `GET /jobs/{id}`

Статус job.

**Ответ `200`:**

```json
{
  "id": 7,
  "status": "processing",
  "created_at": "2026-04-27T12:00:00Z",
  "started_at": "2026-04-27T12:00:01Z",
  "finished_at": null,
  "error": null
}
```

**Статусы:** `queued` → `processing` → `done` | `failed`  
Поле `error` заполняется при `failed`.

---

### `GET /jobs/{id}/result`

Filename результата. Доступен только когда `status = done`.

**Ответ `200`:**

```json
{
  "job_id": 7,
  "filename": "ComfyUI_00007_.png",
  "url": "/files/ComfyUI_00007_.png"
}
```

**Ошибки:** `404 result not ready` — job ещё в `queued` / `processing` / `failed`.

---

### `GET /files/{filename}`

Скачивание PNG. Защищено от path traversal: запрещены `..`, `/`, `\`, скрытые файлы; финальный путь должен лежать внутри `COMFY_OUTPUT_DIR`.

**Ответ:** `image/png` (FileResponse)

**Ошибки:** `400 bad filename` / `400 bad path` — попытка traversal · `404 file not found`

---

## 🗂 Структура проекта

```
content-factory-console/
├── 📁 api/                           # FastAPI приложение
│   ├── app/
│   │   ├── routers/                  # health, generate, jobs, files
│   │   ├── services/                 # CRUD jobs
│   │   ├── main.py                   # FastAPI + CORS + lifespan + limiter
│   │   ├── settings.py               # pydantic-settings → .env
│   │   ├── db.py                     # SQLAlchemy engine + session
│   │   ├── schemas.py                # Pydantic input/output
│   │   └── security.py               # API key dep + slowapi limiter
│   ├── Dockerfile
│   └── requirements.txt
│
├── 📁 worker/                        # Фоновый исполнитель
│   ├── app/
│   │   ├── workflow_templates/
│   │   │   └── base_sdxl_api.json
│   │   ├── worker.py                 # SKIP LOCKED loop
│   │   ├── comfy_client.py           # httpx + tenacity
│   │   ├── settings.py
│   │   └── db.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── 📁 migrations/
│   └── 001_init.sql                  # jobs + job_results + ENUM job_status
│
├── 📁 tests/                         # pytest
│   ├── conftest.py                   # Фикстуры (testdb, client)
│   ├── test_health.py
│   ├── test_generate.py
│   ├── test_files_security.py        # Path traversal (5 кейсов)
│   └── test_worker_pick.py           # SKIP LOCKED конкурентность
│
├── 📁 docs/
│   ├── DEVELOPER.md
│   ├── USER_GUIDE.md
│   └── MIGRATION_R1_TO_R2.md
│
├── 📁 scripts/
│   └── smoke.sh                      # End-to-end проверка одной командой
│
├── 📁 .github/
│   └── workflows/ci.yml              # lint → test → build
│
├── docker-compose.yml                # Release 1 (ComfyUI снаружи)
├── .env.example                      # Шаблон .env
├── .gitignore
├── CHANGELOG.md 
├── SECURITY.md
├── LICENSE
├── CODE_OF_CONDUCT.md
└── README.md  
```

---

## 🧑‍💻 Разработка

### Локальный dev без Docker

```bash
# 1. Виртуальное окружение
python -m venv .venv && source .venv/bin/activate
pip install -r api/requirements.txt -r worker/requirements.txt pytest ruff

# 2. Поднять Postgres локально
docker run -d --name pg -p 5432:5432 \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=app \
  -e POSTGRES_DB=content_factory \
  postgres:16-alpine

# 3. Применить миграции
docker exec -i pg psql -U app -d content_factory < migrations/001_init.sql

# 4. Переменные окружения
export DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/content_factory
export COMFY_URL=http://localhost:8188
export COMFY_OUTPUT_DIR=/path/to/ComfyUI/output

# 5. Запустить сервисы (два терминала)
uvicorn api.app.main:app --reload      # терминал 1
python -m worker.app.worker            # терминал 2
```

### Качество кода

```bash
ruff check api/ worker/ tests/
ruff format api/ worker/ tests/
```

### Добавить новый параметр генерации

Пошаговый рецепт (миграция → schema → service → worker → тест) — `docs/DEVELOPER.md` §7.

---

## 🧪 Тесты и CI

### Запустить локально

```bash
export TEST_DATABASE_URL=postgresql+psycopg://test:test@localhost:5432/test
pytest tests/ -v
```

### Покрытие тестов

| Файл                     | Что тестируется                                                                                                        |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| `test_health.py`         | `/health` отдаёт `200`                                                                                                 |
| `test_generate.py`       | Создание job + Pydantic-валидация (пустой prompt → `422`)                                                              |
| `test_files_security.py` | 5 параметризованных кейсов на path traversal (`..`, `..%2F`, поддиректории, скрытые, пустые)                           |
| `test_worker_pick.py`    | Интеграционный: одна сессия блокирует первую job через `FOR UPDATE`, `pick_one()` обязан взять следующую (SKIP LOCKED) |

### GitHub Actions

При каждом push/PR в ветки `main` и `release-*`:

```
lint  ──►  ruff check  +  ruff format --check
  │
  ▼
test  ──►  реальный Postgres 16 как services
           migrations/001_init.sql
           pytest tests/ -v
  │
  ▼
build ──►  docker compose build
```

---

## 🔒 Безопасность

### Что уже включено в MVP

| Мера                            | Где в коде                                                                                              |
| ------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 🛡️ **Path traversal защита**     | `api/app/routers/files.py` — запрет `..` `///` `\` `.hidden`, резолв пути и проверка `_ROOT in parents` |
| 📂 **Read-only output**          | `docker-compose.yml` — `${COMFY_OUTPUT_HOST}:/comfy_output:ro`                                          |
| 👤 **Non-root user**             | `api/Dockerfile` и `worker/Dockerfile` — `adduser appuser` · `USER appuser`                             |
| 🌐 **Изолированная Docker-сеть** | `networks: internal` · наружу торчит только `8000:8000`                                                 |
| ⚛️ **SKIP LOCKED**               | `worker/app/worker.py::pick_one` — атомарный pickup                                                     |
| ✅ **Валидация входа**           | `api/app/schemas.py` — Pydantic v2 с диапазонами                                                        |
| 🔗 **CORS allowlist**            | `api/app/main.py` — через `ALLOWED_ORIGINS`, не `*`                                                     |
| 🚦 **Rate-limit** (опц.)         | `api/app/security.py::limiter` — slowapi                                                                |
| 🔑 **API key** (опц.)            | `api/app/security.py::require_api_key` — Header `X-API-Key`                                             |
| 🔌 **pool_pre_ping**             | `api/app/db.py` и `worker/app/db.py` — страховка от протухших соединений                                |

> 📋 Полный production-чеклист (HTTPS, gunicorn, secrets, бэкапы, метрики, idempotency) — `docs/DEVELOPER.md` §10.

---

## 🩺 Траблшутинг

| Симптом                                                   | Решение                                                                                                  |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `api` падает с `connection refused` к Postgres            | Проверь `depends_on: condition: service_healthy` в compose; подожди 5–10 сек после `up`                  |
| Worker вечно `processing`                                 | `docker compose logs worker`; проверь `COMFY_SAVE_NODE_ID` в `.env` против `id` SaveImage-узла в шаблоне |
| `Name or service not known: host.docker.internal` (Linux) | В compose должно быть `extra_hosts: ["host.docker.internal:host-gateway"]` для `api` и `worker`          |
| `/files/...` → `404`                                      | `docker compose exec api ls /comfy_output` — должны быть PNG. Если пусто, проверь `COMFY_OUTPUT_HOST`    |
| `422` на `/generate`                                      | Смотри `response.json()["detail"]` — Pydantic пишет точную причину                                       |
| `429 Too Many Requests`                                   | Подними `RATE_LIMIT_PER_MIN` в `.env`                                                                    |
| `403 invalid API key`                                     | Добавь заголовок `-H "X-API-Key: $API_KEY"`                                                              |

---

## 📦 Релизы и Roadmap

| Версия                 | Статус    | Описание                                                                                         |
| ---------------------- | --------- | ------------------------------------------------------------------------------------------------ |
| **v1.0.0** (Release 1) | ✅ Готово  | MVP. ComfyUI запускается отдельно на хосте; контейнеры обращаются по `host.docker.internal:8188` |
| **v2.0.0** (Release 2) | 🔜 Planned | ComfyUI тоже в Docker, GPU passthrough, авто-скачивание моделей через `preflight.py`             |

Полная инструкция миграции R1 → R2 (без потери данных, rollback, параллельный запуск) — [docs/MIGRATION_R1_TO_R2.md](./docs/MIGRATION_R1_TO_R2.md).

История версий по [Keep a Changelog](https://keepachangelog.com/) + [SemVer](https://semver.org/) — [CHANGELOG.md](./CHANGELOG.md).

---

## 📚 Документация

| Документ                                                     | Аудитория             | Содержание                                                                                                          |
| ------------------------------------------------------------ | --------------------- | ------------------------------------------------------------------------------------------------------------------- |
| [`docs/USER_GUIDE.md`](./docs/USER_GUIDE.md)                 | Конечный пользователь | Пошаговая установка, примеры curl/Python, частые проблемы                                                           |
| [`docs/DEVELOPER.md`](./docs/DEVELOPER.md)                   | Разработчик           | Архитектура, локальный dev, инварианты, добавление параметров/шаблонов, миграции, релизный flow, production-чеклист |
| [`docs/MIGRATION_R1_TO_R2.md`](./docs/MIGRATION_R1_TO_R2.md) | DevOps / разработчик  | Переход с R1 на R2 без потери данных, rollback, параллельный запуск                                                 |
| [`CHANGELOG.md`](./CHANGELOG.md)                             | Все                   | История версий по Keep a Changelog + SemVer                                                                         |
| [`SECURITY.md`](./SECURITY.md)                               | Все                   | Политика безопасности: поддерживаемые версии, как сообщить об уязвимости, сроки ответа                              |
| [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md)                 | Контрибьюторы         | Contributor Covenant 2.1                                                                                            |

---

## 🤝 Contributing

PR-ы и Issues приветствуются! Перед началом:

1. 📖 Прочитай [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md) — мы за дружелюбное и инклюзивное сообщество.
2. 💬 Создай **Issue** с описанием проблемы или фичи перед большим PR.
3. 🌿 Ветка от `main` или `release-*`, имя по формату: `feat/...`, `fix/...`, `docs/...`
4. ✅ Прогони локально:
   ```bash
   ruff check && ruff format --check && pytest tests/ -v
   ```
5. 🚦 PR должен пройти CI (`lint → test → build`).
6. 📝 Описание PR — что и зачем; ссылки на issue; примеры curl/скриншоты, если меняешь API.

> 💡 Хочешь предложить большую архитектурную фичу? Сначала открой **Discussion** на GitHub — обсудим, прежде чем писать код.

---

## 🛡️ Сообщить об уязвимости

Если нашёл уязвимость — **не открывай публичный Issue**. Используй приватные каналы:

- 🛡️ **GitHub Security Advisory:** [security/advisories/new](https://github.com/Bogdan-95/content-factory-console/security/advisories/new) *(предпочтительный)*
- 📧 **Email:** [b95rengo@gmail.com](mailto:b95rengo@gmail.com)
- 💬 **Telegram:** [@bodya_95](https://t.me/bodya_95)

Полная политика, сроки ответа, что считается уязвимостью — [`SECURITY.md`](./SECURITY.md).

---

## 📜 Лицензия

Распространяется под лицензией [Apache License 2.0](./LICENSE).

|     |                                                                |
| --- | -------------------------------------------------------------- |
| ✅   | Свободное коммерческое использование, модификация, дистрибуция |
| ✅   | Можно использовать как часть закрытых проектов                 |
| ⚠️   | Сохраняй copyright-нотис и текст лицензии при дистрибуции      |
| ⚠️   | При значимых изменениях — указывай это в `NOTICE` файле        |
| ❌   | Никакой гарантии — used at your own risk                       |

Copyright © 2026 Bogdan. License Apache-2.0.

---

## 👤 Автор

<div align="center">

**Bogdan** · backend-разработчик

[![GitHub](https://img.shields.io/badge/GitHub-Bogdan--95-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/Bogdan-95)
[![Telegram](https://img.shields.io/badge/Telegram-@bodya__95-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://t.me/bodya_95)
[![Email](https://img.shields.io/badge/Email-b95rengo@gmail.com-D14836?style=flat-square&logo=gmail&logoColor=white)](mailto:b95rengo@gmail.com)

*Обратная связь, вопросы по проекту, предложения работы, фидбек — пиши в Telegram или на почту. Отвечаю обычно в течение суток.*

</div>

---

<div align="center">

⭐ Если проект был полезен — поставь звезду на GitHub, это помогает другим его найти.

</div>