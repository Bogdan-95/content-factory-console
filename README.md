<div align="center">

# 🏭 Content Factory Console

</div>

<p align="center">
  <strong>Backend‑обвязка над ComfyUI: REST API + очередь задач в PostgreSQL + асинхронный worker.<br>Генерация изображений Stable Diffusion XL одной командой <code>docker compose up</code>.</strong>
</p>

<div align="center">

[![Release v2.0.0](https://img.shields.io/badge/release-v2.0.0-blue)](./CHANGELOG.md)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-latest-orange?logo=comfyui&logoColor=white)](https://github.com/comfyanonymous/ComfyUI)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue?style=flat-square&logo=apache&logoColor=white)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker_Compose-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Alembic-1.14-blueviolet?style=flat-square&logo=python&logoColor=white)](https://alembic.sqlalchemy.org/)
[![Ruff](https://img.shields.io/badge/code_style-ruff-D7FF64?style=flat-square&logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)

---

<div align="center">

[🚀 Быстрый старт](#-быстрый-старт) ·
[📡 API](#-api) ·
[🏗 Архитектура](#-архитектура) ·
[🖼️ Скриншоты](#️-скриншоты) ·
[📦 Релизы и Roadmap](#-релизы-и-roadmap) ·
[📋 CHANGELOG](./CHANGELOG.md) ·
[🔒 Security](./SECURITY.md)

</div>

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
| ✅   | Очередь на чистом PostgreSQL (без Redis / Celery / RabbitMQ)         |

---

## 📑 Содержание

- [🏭 Content Factory Console](#-content-factory-console)
  - [🎯 Что это и зачем](#-что-это-и-зачем)
  - [📑 Содержание](#-содержание)
  - [✨ Возможности](#-возможности)
  - [📋 Требования](#-требования)
    - [Минимальные (проверено на практике)](#минимальные-проверено-на-практике)
    - [Рекомендованные](#рекомендованные)
    - [Проверено на](#проверено-на)
  - [🚀 Быстрый старт](#-быстрый-старт)
    - [1. Клонировать](#1-клонировать)
    - [2. Настроить окружение](#2-настроить-окружение)
    - [3. Поднять сервисы](#3-поднять-сервисы)
    - [4. Проверить](#4-проверить)
    - [POST /generate](#post-generate)
    - [Request body:](#request-body)
    - [Поля запроса:](#поля-запроса)
    - [GET /jobs/{id}](#get-jobsid)
    - [GET /jobs/{id}/result](#get-jobsidresult)
    - [GET /files/{filename}](#get-filesfilename)
  - [🖼️ Скриншоты](#️-скриншоты)
  - [⚙️ Конфигурация](#️-конфигурация)
  - [🏗 Архитектура](#-архитектура)
    - [Жизненный цикл Job](#жизненный-цикл-job)
  - [🔧 Стек](#-стек)
    - [Слой технологий](#слой-технологий)
  - [🗂 Структура проекта](#-структура-проекта)
  - [🧑‍💻 Разработка](#-разработка)
    - [Локальный dev без Docker](#локальный-dev-без-docker)
    - [Качество кода](#качество-кода)
  - [🧪 Тесты и CI](#-тесты-и-ci)
    - [Запустить локально](#запустить-локально)
  - [Покрытие тестов](#покрытие-тестов)
  - [GitHub Actions](#github-actions)
  - [🔒 Безопасность](#-безопасность)
    - [Что уже включено](#что-уже-включено)
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
- 🎨 **ComfyUI в Docker** (Release 2): GPU‑проброс через `nvidia-container-toolkit`, авто‑скачивание моделей через `preflight.py`.
- 🐳 **Docker Compose:** Postgres 16 + ComfyUI + API + Worker + preflight — одной командой, с healthcheck и зависимостями.
- ✅ **Тесты + CI:** pytest с реальным Postgres в GitHub Actions services + ruff lint/format + `docker compose build`.
- 🔒 **Безопасность из коробки:** защита от path traversal, read-only том для output, non-root user, изолированная Docker-сеть, валидация Pydantic v2, обязательный API-key и rate-limit.
- 📘 **Документация на трёх уровнях:** README (продажа), `docs/DEVELOPER.md` (внутрь), `docs/USER_GUIDE.md` (наружу).
- 📦 **Alembic** для миграций БД — автоматическое применение при старте API.

---

## 📋 Требования

### Минимальные (проверено на практике)

| Компонент                    | Требование                                                      |
| ---------------------------- | --------------------------------------------------------------- |
| **ОС**                       | Ubuntu 22.04+ / Windows 11 + WSL2                               |
| **Docker**                   | Engine 24+ с плагином `docker compose`                          |
| **RAM**                      | 16 ГБ (система + модель + контейнеры)                           |
| **Диск**                     | 30 ГБ свободного места (модель 6.5 ГБ + образы Docker + output) |
| **GPU**                      | NVIDIA с 8 ГБ VRAM (RTX 2060 Super / 3060 / 4060 / 5060 и выше) |
| **NVIDIA Container Toolkit** | обязателен для проброса GPU в Docker                            |

### Рекомендованные

| Компонент | Требование                                     |
| --------- | ---------------------------------------------- |
| **RAM**   | 32 ГБ (для комфортной работы с большими batch) |
| **GPU**   | 12+ ГБ VRAM (для high-res 2048×2048)           |

### Проверено на

```text 
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

***Отредактируйте .env:***

```bash
POSTGRES_PASSWORD=<придумайте пароль>
API_KEY=<сгенерируйте ключ: openssl rand -hex 32>
ALLOWED_ORIGINS=http://localhost:3000  # или ваш фронтенд
```

> **Важно:**  Все остальные параметры уже предустановлены для Release 2. Меняйте их только при необходимости.

### 3. Поднять сервисы

```bash
docker compose up --build
```

***При первом запуске:***

- preflight скачает модель SDXL Base (~6.5 ГБ, 5–20 минут).

- После появления сообщения ✅ preflight: all models ready запустится ComfyUI.

- API станет доступен на http://localhost:8000.

Следите за логами: `docker compose logs -f preflight`.

### 4. Проверить

```bash
# Health check
curl http://localhost:8000/health
# {"ok": true}

# Создать задачу (замените API_KEY на ваш ключ)
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"prompt":"a beautiful sunset, masterpiece, 8k","steps":20}'
# {"job_id": 1, "status": "queued"}

# Опрос статуса (queued → processing → done)
curl -H "X-API-Key: $API_KEY" http://localhost:8000/jobs/1

# Получить имя файла
curl -H "X-API-Key: $API_KEY" http://localhost:8000/jobs/1/result

# Скачать PNG
curl -O http://localhost:8000/files/ComfyUI_00001_.png
```

```markdown
> 💡 **Или всё одной командой через smoke-скрипт:**
>
> ```bash
> ./scripts/smoke.sh
> ```

---

## 📡 API

- 📖 Полный Swagger UI: http://localhost:8000/docs
- 📖 ReDoc: http://localhost:8000/redoc

Важно: Все эндпоинты, кроме `/health`, требуют заголовок `X-API-Key` с вашим ключом.

### GET /health

Liveness-пинг для k8s / uptime-мониторинга.

```text
200 OK
{"ok": true}
```

### POST /generate

Создаёт задачу на генерацию. Возвращает `job_id` сразу, не дожидаясь ComfyUI.

### Request body:

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

### Поля запроса:

| Поле       | Тип    | Диапазон        | По умолчанию     |
| ---------- | ------ | --------------- | ---------------- |
| `prompt`   | string | 1…2000 символов | *обязательно*    |
| `negative` | string | 0…2000 символов | `""`             |
| `width`    | int    | 256…2048        | `1024`           |
| `height`   | int    | 256…2048        | `1024`           |
| `steps`    | int    | 1…80            | `20`             |
| `cfg`      | float  | 0…30            | `7.0`            |
| `seed`     | int    | ≥ −1            | `-1` (случайный) |

Ответ 202:

```json
{"job_id": 7, "status": "queued"}
```

***Ошибки:*** `422` — Pydantic-валидация · `429` — rate-limit · `403` — bad API key

### GET /jobs/{id}

Статус job.

Ответ `200`:

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

> [!TIP] Статусы: `queued` → `processing` → `done` | `failed`

Поле `error` заполняется при `failed`.

### GET /jobs/{id}/result

Filename результата. Доступен только когда `status = done`.

Ответ `200`:

```json
{
  "job_id": 7,
  "filename": "ComfyUI_00007_.png",
  "url": "/files/ComfyUI_00007_.png"
}
```

> [!WARNING] Ошибки: 404 result not ready — job ещё в queued / processing / failed.

### GET /files/{filename}

Скачивание PNG. Защищено от path traversal: запрещены `.., /, \`, скрытые файлы; финальный путь должен лежать внутри `COMFY_OUTPUT_DIR.`

***Ответ***: image/png (FileResponse)

Ошибки: `400 bad filename` / `400 bad path` — попытка traversal    `404 file not found`

---

## 🖼️ Скриншоты

<div align="center">

![Swagger UI – успешный POST /generate](docs/screenshots/swagger_generate.png)

*Swagger UI: авторизация по API-ключу и успешный вызов генерации*

![Результат генерации](docs/screenshots/result_example.png)

*Сгенерированное изображение (SDXL, steps=25)*

</div>

---

## ⚙️ Конфигурация

Все настройки задаются в файле [`.env`](.env.example).  
Полный список переменных с пояснениями:

| Переменная                       | Значение по умолчанию                                      | Назначение                                                                                                     |
| -------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `POSTGRES_PASSWORD`              | *обязательно*                                              | Пароль пользователя БД `app`. В production генерируйте: `openssl rand -base64 24 \| tr -d '/+=' \| cut -c1-24` |
| `DATABASE_URL`                   | `postgresql+psycopg://app:…@postgres:5432/content_factory` | URL подключения к базе данных (драйвер psycopg 3)                                                              |
| `COMFY_URL`                      | `http://comfyui:8188`                                      | Адрес ComfyUI внутри Docker-сети                                                                               |
| `COMFY_SAVE_NODE_ID`             | `9`                                                        | ID узла `SaveImage` в используемом workflow                                                                    |
| `API_KEY`                        | *обязательно*                                              | Ключ для доступа к API. В production генерируйте: `openssl rand -hex 32`                                       |
| `RATE_LIMIT_PER_MIN`             | `30`                                                       | Максимальное число запросов к `/generate` в минуту с одного IP                                                 |
| `ALLOWED_ORIGINS`                | `http://localhost:3000`                                    | Разрешённые источники для CORS (через запятую)                                                                 |
| `WORKER_POLL_INTERVAL_SEC`       | `2`                                                        | Период опроса очереди worker'ом                                                                                |
| `WORKER_COMFY_POLL_INTERVAL_SEC` | `2`                                                        | Период опроса истории ComfyUI                                                                                  |
| `WORKER_COMFY_TIMEOUT_SEC`       | `600`                                                      | Максимальное время выполнения одной генерации                                                                  |

> **Важно:** значения `POSTGRES_PASSWORD` и `API_KEY` **не должны** оставаться дефолтными при реальном использовании.

---

## 🏗 Архитектура

```mermaid
graph LR
    A["🖥️ Client"] -->|"POST /generate"| B["⚡ FastAPI :8000"]
    B -->|"INSERT jobs"| C[("🗄️ PostgreSQL")]
    D["⚙️ Worker"] -->|"FOR UPDATE SKIP LOCKED"| C
    D -->|"POST /prompt"| E["🎨 ComfyUI :8188 (Docker)"]
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
POST http://comfyui:8188/prompt (подставлен workflow)
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

### Слой технологий

| Слой                | Технологии                                         |
| ------------------- | -------------------------------------------------- |
| 🐍 **Язык**          | Python 3.12                                        |
| 🌐 **Web**           | FastAPI 0.115, Pydantic v2, pydantic-settings 2.6  |
| 🗄️ **БД**            | PostgreSQL 16, SQLAlchemy 2.0, psycopg v3, Alembic |
| ⏳ **Очередь**       | Postgres `FOR UPDATE SKIP LOCKED` (zero-broker)    |
| 📡 **HTTP-клиент**   | httpx 0.27 + tenacity 9 (экспоненциальный backoff) |
| ✅ **Тесты**         | pytest, FastAPI TestClient, реальный Postgres в CI |
| 🧹 **Качество кода** | ruff (lint + format), type hints везде             |
| 🐳 **Контейнеры**    | Docker, docker-compose, NVIDIA Container Toolkit   |
| 🚦 **CI**            | GitHub Actions: lint → test → build                |
| 🤖 **AI-интеграция** | ComfyUI HTTP API + SDXL Base 1.0                   |

---

## 🗂 Структура проекта

```text
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
│   ├── prestart.sh                   # Запуск Alembic перед стартом API
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
├── 📁 comfyui/                       # Docker-образ ComfyUI
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── 📁 scripts/                       # Вспомогательные скрипты
│   ├── smoke.sh                      # End-to-end smoke test
│   ├── preflight.py                  # Авто‑скачивание моделей
│   ├── models_map.json               # Карта моделей
│   └── Dockerfile.preflight
│
├── 📁 migrations_alembic/            # Alembic миграции
│   ├── env.py
│   ├── versions/
│   │   └── 66a1a1ca5e9d_initial.py
│   └── script.py.mako
│
├── 📁 tests/                         # pytest
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_generate.py
│   ├── test_files_security.py
│   └── test_worker_pick.py
│
├── 📁 docs/                          # Документация
│   ├── DEVELOPER.md
│   ├── USER_GUIDE.md
│   ├── MIGRATION_R1_TO_R2.md
│   └── screenshots/
│       ├── swagger_generate.png
│       ├── result_example.png
│       └── comfyui_gui.png
│
├── 📁 .github/
│   └── workflows/ci.yml
│
├── alembic.ini
├── docker-compose.yml
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── SECURITY.md
├── LICENSE
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

# 3. Применить миграции Alembic
export DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/content_factory
alembic upgrade head

# 4. Переменные окружения
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

```markdown
### Добавить новый параметр генерации

Пошаговый рецепт (миграция → schema → service → worker → тест) — [docs/DEVELOPER.md §7](./docs/DEVELOPER.md#7-как-добавить-новый-параметр-генерации).
```

## 🧪 Тесты и CI

### Запустить локально

```bash
export TEST_DATABASE_URL=postgresql+psycopg://test:test@localhost:5432/test
pytest tests/ -v
```

## Покрытие тестов

| Файл                     | Что тестируется                                                                                                        |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| `test_health.py`         | `/health` отдаёт `200`                                                                                                 |
| `test_generate.py`       | Создание job + Pydantic-валидация (пустой prompt → `422`)                                                              |
| `test_files_security.py` | 5 параметризованных кейсов на path traversal (`..`, `..%2F`, поддиректории, скрытые, пустые)                           |
| `test_worker_pick.py`    | Интеграционный: одна сессия блокирует первую job через `FOR UPDATE`, `pick_one()` обязан взять следующую (SKIP LOCKED) |

## GitHub Actions

При каждом push/PR в ветки `main` и `release-*`:

```text
lint  ──►  ruff check  +  ruff format --check
  │
  ▼
test  ──►  реальный Postgres 16 как services, pytest tests/ -v
  │
  ▼
build ──►  docker compose build
```

---

## 🔒 Безопасность

### Что уже включено

| Мера                            | Где в коде                                                                                              |
| ------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 🛡️ **Path traversal защита**     | `api/app/routers/files.py` — запрет `..` `///` `\` `.hidden`, резолв пути и проверка `_ROOT in parents` |
| 📂 **Read-only output**          | `docker-compose.yml` — `comfy_output:/comfy_output:ro`                                                  |
| 👤 **Non-root user**             | `api/Dockerfile` и `worker/Dockerfile` — `adduser appuser` · `USER appuser`                             |
| 🌐 **Изолированная Docker-сеть** | `networks: internal` · наружу торчит только `8000:8000`                                                 |
| ⚛️ **SKIP LOCKED**               | `worker/app/worker.py::pick_one` — атомарный pickup                                                     |
| ✅ **Валидация входа**           | `api/app/schemas.py` — Pydantic v2 с диапазонами                                                        |
| 🔗 **CORS allowlist**            | `api/app/main.py` — через `ALLOWED_ORIGINS`, не `*`                                                     |
| 🚦 **Rate-limit**                | `api/app/security.py::limiter` — slowapi                                                                |
| 🔑 **API key**                   | `api/app/security.py::require_api_key` — Header `X-API-Key`                                             |
| 🔌 **pool_pre_ping**             | `api/app/db.py` и `worker/app/db.py` — страховка от протухших соединений                                |

> 📋 Полный production-чеклист (HTTPS, gunicorn, secrets, бэкапы, метрики, idempotency) — [`docs/DEVELOPER.md`](./docs/DEVELOPER.md) §10.

---

## 🩺 Траблшутинг

| Симптом                                        | Решение                                                                                                  |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `api` падает с `connection refused` к Postgres | Проверь `depends_on: condition: service_healthy` в compose; подожди 5–10 сек после `up`                  |
| Worker вечно `processing`                      | `docker compose logs worker`; проверь `COMFY_SAVE_NODE_ID` в `.env` против `id` SaveImage-узла в шаблоне |
| `/files/...` → `404`                           | `docker compose exec api ls /comfy_output` — должны быть PNG. Если пусто, проверь работу ComfyUI         |
| `422` на `/generate`                           | Смотри `response.json()["detail"]` — Pydantic пишет точную причину                                       |
| `429 Too Many Requests`                        | Подними `RATE_LIMIT_PER_MIN` в `.env`                                                                    |
| `403 invalid API key`                          | Добавь заголовок `-H "X-API-Key: $API_KEY"`                                                              |
| GPU не виден (R2)                              | `docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi` должен показать GPU          |
| Preflight завис на скачивании модели           | Проверь интернет; можно вручную положить файл в `comfyui/models/checkpoints/` и скопировать в том        |

---

## 📦 Релизы и Roadmap

| Версия                 | Статус   | Описание                                                                                         |
| ---------------------- | -------- | ------------------------------------------------------------------------------------------------ |
| **v1.0.0** (Release 1) | ✅ Готово | MVP. ComfyUI запускается отдельно на хосте; контейнеры обращаются по `host.docker.internal:8188` |
| **v2.0.0** (Release 2) | ✅ Готово | ComfyUI в Docker, GPU-проброс, Alembic, авто‑скачивание моделей, обязательный API‑ключ           |

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

5. 🚦 PR должен пройти CI (lint → test → build).
6. 📝 Описание PR — что и зачем; ссылки на issue; примеры curl/скриншоты, если меняешь API.

>💡 Хочешь предложить большую архитектурную фичу? Сначала открой **Discussion** на GitHub — обсудим, прежде чем писать код.

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

---

## 👤 Автор

<div align="center">

**Bogdan** · backend‑разработчик

[![GitHub](https://img.shields.io/badge/GitHub-Bogdan--95-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/Bogdan-95)
[![Telegram](https://img.shields.io/badge/Telegram-@bodya__95-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://t.me/bodya_95)
[![Email](https://img.shields.io/badge/Email-b95rengo%40gmail.com-D14836?style=flat-square&logo=gmail&logoColor=white)](mailto:b95rengo@gmail.com)

*Обратная связь, вопросы по проекту, предложения работы, фидбек — пишите в Telegram или на почту. Отвечаю обычно в течение суток.*

</div>

<div align="center">

⭐ Если проект был полезен — поставьте звезду на GitHub, это помогает другим его найти.

</div>
