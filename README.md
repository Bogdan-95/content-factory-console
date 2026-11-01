# Content Factory Console

Self-hosted сервис для постановки и обработки задач генерации изображений через ComfyUI.

REST API принимает задания, PostgreSQL хранит очередь, а отдельный Worker отправляет workflow в ComfyUI и сохраняет результат выполнения.

> Портфолио-проект. Для реального публичного развёртывания потребуются дополнительные operational- и security-проверки, описанные в разделе «Ограничения».

## Возможности

- FastAPI REST API для создания задач и получения их статусов.
- Очередь задач на PostgreSQL без Redis/Celery.
- Захват заданий через `SELECT ... FOR UPDATE SKIP LOCKED`.
- Отдельные API и Worker контейнеры.
- Интеграция Worker с ComfyUI API.
- Миграции PostgreSQL через Alembic.
- Docker Compose для локального запуска.
- Pytest, Ruff и GitHub Actions.

## Архитектура

```text
Client
  |
  v
FastAPI API -----> PostgreSQL jobs
                       |
                       v
                 Worker (SKIP LOCKED)
                       |
                       v
                    ComfyUI
                       |
                       v
                 Generated image
```

Worker атомарно выбирает ожидающую задачу и переводит её в `processing`. PostgreSQL позволяет нескольким экземплярам Worker конкурировать за задания, пропуская строки, уже заблокированные другой транзакцией.

## Стек

| Область | Технологии |
|---|---|
| API | Python 3.12, FastAPI, Pydantic |
| Database | PostgreSQL 16, SQLAlchemy 2, psycopg 3 |
| Migrations | Alembic |
| Worker | Python, SQLAlchemy, httpx |
| Runtime | Docker, Docker Compose |
| Quality | Pytest, Ruff, GitHub Actions |

## API

| Метод | Endpoint | Назначение |
|---|---|---|
| `POST` | `/generate` | Создать задачу |
| `GET` | `/jobs/{id}` | Получить статус и детали |
| `GET` | `/jobs/{id}/result` | Получить имя файла результата |
| `GET` | `/files/{filename}` | Скачать изображение |
| `GET` | `/health` | Проверить доступность API |

Swagger UI после запуска: [http://localhost:8000/docs](http://localhost:8000/docs).

## Быстрый старт

Требуются Docker Compose, NVIDIA GPU и NVIDIA Container Toolkit для запуска ComfyUI с GPU.

```bash
git clone https://github.com/Bogdan-95/content-factory-console.git
cd content-factory-console
cp .env.example .env
```

Перед запуском замени значения секретов в `.env`:

- `POSTGRES_PASSWORD` — пароль PostgreSQL;
- `API_KEY` — случайный ключ API.

Сгенерировать API-ключ можно командой:

```bash
openssl rand -hex 32
```

Запуск:

```bash
docker compose up --build
```

Первый запуск может занять время: сервис ComfyUI загружает модель Stable Diffusion XL. API будет доступен на порту `8000`.

Пример создания задания:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"prompt":"a mountain landscape at sunrise","steps":20}'
```

Проверить статус:

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/jobs/1
```

## Тестирование

Тесты используют отдельную PostgreSQL-базу с именем `test`. Конфигурация намеренно откажется выполнять миграции, если URL указывает на другую базу или не локальный хост.

Создай отдельную тестовую БД и укажи URL:

```bash
export TEST_DATABASE_URL=postgresql+psycopg://test:test@localhost:5432/test
pytest tests/ -v
```

Тестовая схема создаётся через Alembic migrations. Интеграционные тесты проверяют API и реальный вызов функции захвата задания Worker'а с блокировкой PostgreSQL.

## CI

GitHub Actions выполняет:

1. Ruff lint и форматирование;
2. миграции и Pytest на отдельном PostgreSQL 16 service;
3. сборку Docker Compose.

## Структура

```text
api/                 FastAPI application
worker/              ComfyUI job worker
migrations_alembic/  PostgreSQL schema migrations
tests/               API and worker tests
scripts/             Smoke and setup helpers
docs/                User, developer and migration guides
docker-compose.yml
```

## Ограничения и дальнейшая работа

- Полный цикл генерации требует доступного ComfyUI и совместимой GPU-среды; CI проверяет сборку контейнеров, но не выполняет реальную генерацию на GPU.
- Тесты Worker должны проверять не только SQL-оператор, но и функции приложения; тест захвата задания делает именно это.
- Нужны дополнительные тесты восстановления зависших задач, повторных попыток, обработки ошибок ComfyUI и отказов БД.
- Перед production-развёртыванием следует отдельно проверить rate limiting, хранение и ротацию ключей, сетевые границы, retention результатов и мониторинг.

## Автор

Bogdan Rengo · [GitHub](https://github.com/Bogdan-95)
