# Changelog

Все значимые изменения проекта документируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версионирование следует [Semantic Versioning](https://semver.org/lang/ru/).

---

## [Unreleased]

### Planned

- Watchdog для зависших `processing` (возврат в `queued` после N минут).
- Идемпотентность `/generate` через `idempotency_key` + unique‑индекс.
- Prometheus metrics + Grafana dashboard.
- Web UI на Next.js.
- Поддержка нескольких workflow‑шаблонов (SD 1.5, SDXL, Flux).

---

## [2.0.0] — Planned

### Added

- Сервис `comfyui` в `docker-compose.yml` с GPU passthrough через `nvidia-container-toolkit`.
- `scripts/preflight.py` — авто‑скачивание моделей с SHA256‑проверкой целостности.
- `scripts/models_map.json` — декларативный конфиг моделей (checkpoints / vae / loras).
- `scripts/Dockerfile.preflight` — образ для одноразового сервиса‑скачивателя.
- Named volume `comfy_models` — модели переживают `docker compose down`.
- Named volume `comfy_output` — PNG‑результаты, общий между `comfyui` и `api`.

### Changed

- `COMFY_URL` теперь по умолчанию `http://comfyui:8188` (внутри compose сети).
- Удалён `COMFY_OUTPUT_HOST` — output живёт в named volume.
- `docker-compose.yml` полностью переписан под новую архитектуру.
- `worker.py::_apply_params` — стабильный seed (если `seed=-1`, генерируется случайный, но логируется).

### Removed

- Зависимость от `host.docker.internal` (но `extra_hosts` оставлен на случай гибридного режима).
- Bind‑mount хост‑папки `output/` (заменён на named volume).

### Migration

- См. подробную инструкцию: docs/MIGRATION_R1_TO_R2.md
- TL;DR пути: `pg_dump` → archive PNG → `down` → `checkout main` → edit `.env` → `up --build` → restore PNG → smoke test.

---

## [1.0.0] — 2026‑04‑27

Первый рабочий релиз — MVP «пульта контент‑завода».

### Added

- **API (FastAPI 0.115):** `/health`, `POST /generate`, `GET /jobs/{id}`, `GET /jobs/{id}/result`, `GET /files/{name}`.
- **Очередь в Postgres** через `SELECT … FOR UPDATE SKIP LOCKED` — без Redis/Celery/RabbitMQ.
- **Worker** на httpx + tenacity: подставляет промпт в API‑формат workflow ComfyUI, опрашивает `/history/{prompt_id}`, сохраняет filename. Экспоненциальные ретраи (5 попыток, backoff 0.5–8 сек).
- **Docker Compose:** Postgres 16 + API + Worker — одной командой, с healthcheck для БД и `depends_on: condition: service_healthy`.
- **ComfyUI запускается на хосте** (`python main.py --listen 0.0.0.0`), контейнеры достают его по `host.docker.internal:8188` (через `extra_hosts: host-gateway`).
- **Read‑only монт** `${COMFY_OUTPUT_HOST}:/comfy_output:ro` в API — даже при RCE невозможно писать в output.
- **Защита от path traversal** в `/files/{name}`: запрет `..`, `/`, `\`, скрытых файлов; резолв пути и проверка `_ROOT in parents`.
- **API‑ключ** через `X-API-Key` header (опционально, готов к prod через `dependencies=[Depends(require_api_key)]`).
- **Rate‑limit** через `slowapi` (по умолчанию 30 req/min на IP).
- **CORS allowlist** через `ALLOWED_ORIGINS` в `.env` — никаких `*`.
- **Pydantic v2** валидация входа: длины, диапазоны для `width`, `height`, `steps`, `cfg`, `seed`.
- **Non‑root user** (`appuser`) в обоих образах.
- **`pool_pre_ping=True`** в обоих SQLAlchemy‑engine — страховка от протухших соединений.
- **pytest 4 файла:** `test_health.py`, `test_generate.py`, `test_files_security.py` (5 параметризованных кейсов), `test_worker_pick.py` (интеграционный SKIP LOCKED).
- **GitHub Actions CI:** lint (`ruff check` + `ruff format --check`) → test (Postgres 16 как `services`, реальная миграция) → build (`docker compose build`).
- **Документация на трёх уровнях:** `README.md` (продажа), `docs/DEVELOPER.md` (внутрь), `docs/USER_GUIDE.md` (наружу).
- **Smoke‑скрипт** `scripts/smoke.sh` — end‑to‑end проверка одной командой.

### Security

- Path traversal защита в `/files/{name}`.
- Read‑only output volume.
- Изолированная Docker‑сеть `internal`, наружу только `8000:8000`.
- Non‑root user в контейнерах.
- `.env` в `.gitignore`, в репо только `.env.example`.

### Known issues

- ComfyUI на хосте — единая точка отказа. Решается в R2.
- Нет идемпотентности `/generate` — повторный POST создаст дубль job. Решается в R3.
- Нет watchdog для зависших `processing`. Решается в R3.
- Default `API_KEY=dev-local-key-change-me` — нельзя оставлять в проде. Документировано в README.

---

## Ссылки сравнения

```
[Unreleased]: https://github.com/Bogdan-95/content-factory-console/compare/v2.0.0...HEAD
[2.0.0]:      https://github.com/Bogdan-95/content-factory-console/compare/v1.0.0...v2.0.0
[1.0.0]:      https://github.com/Bogdan-95/content-factory-console/releases/tag/v1.0.0
```