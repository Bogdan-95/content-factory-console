# Content Factory Console

Self-hosted сервис для постановки и обработки задач генерации изображений через ComfyUI.

Проект реализует REST API, очередь заданий на PostgreSQL и отдельный Worker, который взаимодействует с ComfyUI и сохраняет результаты генерации.

## Основные возможности

- REST API на FastAPI для создания задач и проверки их статуса.
- Очередь задач на PostgreSQL без Redis и Celery.
- Конкурентное получение заданий через `SELECT ... FOR UPDATE SKIP LOCKED`.
- Отдельный процесс Worker для обработки задач.
- Интеграция с ComfyUI API.
- Сохранение результатов генерации и статусов выполнения.
- Миграции базы данных через Alembic.
- Контейнеризация с Docker Compose.

## Архитектура

```text
Client
  |
  v
FastAPI
  |
  v
PostgreSQL
  |
  v
Worker
  |
  v
ComfyUI
  |
  v
Generated Image
```

Несколько экземпляров Worker могут получать задания из общей очереди. `SKIP LOCKED` позволяет не блокировать обработку задач, уже захваченных другим Worker.

## Технологический стек

- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy 2.0
- PostgreSQL 16
- Alembic
- Docker / Docker Compose
- Pytest
- Ruff
- GitHub Actions

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/generate` | Создание задачи |
| GET | `/jobs/{id}` | Получение статуса |
| GET | `/jobs/{id}/result` | Получение результата |
| GET | `/files/{filename}` | Скачивание изображения |
| GET | `/health` | Проверка состояния API |

Swagger: `http://localhost:8000/docs`

## Запуск

Требуются Docker Compose, поддерживаемая NVIDIA GPU и NVIDIA Container Toolkit.

```bash
git clone https://github.com/Bogdan-95/content-factory-console.git
cd content-factory-console

cp .env.example .env
```

Укажи необходимые параметры окружения, включая `POSTGRES_PASSWORD` и `API_KEY`.

Запуск:

```bash
docker compose up --build
```

После первоначальной загрузки модели API будет доступен на порту `8000`.

## Тестирование

```bash
export TEST_DATABASE_URL=postgresql+psycopg://test:test@localhost:5432/test

pytest tests/ -v
```

GitHub Actions выполняет:

- Ruff lint и format checks;
- тестирование с PostgreSQL 16;
- сборку Docker Compose.

Автоматизированные тесты проверяют API, валидацию запросов, защиту файловых путей и поведение блокировок PostgreSQL. Полный цикл генерации через реальный ComfyUI требует отдельного интеграционного тестирования.

## Структура

```text
api/
worker/
tests/
migrations_alembic/
docs/
scripts/
docker-compose.yml
alembic.ini
```

## Назначение проекта

Портфолио-проект, демонстрирующий работу с REST API, очередями задач, транзакциями PostgreSQL, конкурентным доступом к данным и контейнеризацией.

## Автор

Bogdan Rengo

GitHub: https://github.com/Bogdan-95
