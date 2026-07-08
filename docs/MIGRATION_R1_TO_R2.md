# Миграция Release 1 → Release 2

## TL;DR

- **R1** = ComfyUI на хосте + контейнеры обращаются по `host.docker.internal:8188`.
- **R2** = ComfyUI **тоже** в Docker, GPU passthrough, named volumes.
- **R1 не «слетает» после R2** — он живёт в теге `v1.0.0` и ветке `release-1`. Откат = `git checkout v1.0.0 && docker compose up -d`.
- **Полный путь миграции:** backup Postgres → archive PNG → `down` → checkout main → edit `.env` → `up --build` → restore PNG → smoke test.
- **Время простоя:** ~5–10 минут на пустом проекте, ~15–30 минут с восстановлением 1000+ PNG.

## Что меняется (диф R1 → R2)

| Аспект               | R1                                  | R2                                             |
| -------------------- | ----------------------------------- | ---------------------------------------------- |
| `COMFY_URL`          | `http://host.docker.internal:8188`  | `http://comfyui:8188`                          |
| Модели               | Вручную скачаны в `ComfyUI/models/` | Named volume + `preflight.py` авто‑качает      |
| Запуск               | 2 терминала (ComfyUI + compose)     | 1 команда `docker compose up`                  |
| Зависимость от хоста | Критична (ComfyUI должен крутиться) | Минимальна (только `nvidia-container-toolkit`) |

## Что остаётся неизменным

- API endpoints (`/health`, `/generate`, `/jobs/{id}`, `/jobs/{id}/result`, `/files/{name}`).
- Схема БД (jobs + job_results + ENUM `job_status`).
- Pydantic‑модели входа/выхода — клиенты не ломаются.
- Worker‑логика (SKIP LOCKED, шаблон workflow, ретраи).
- Тесты pytest и CI workflow.
- API‑ключ, rate‑limit, CORS — все настройки через `.env`.

## Шаги миграции (production)

### Шаг 0 — Готовность

- [ ]  У тебя есть бэкап Postgres (`pg_dump`).
- [ ]  У тебя установлен `nvidia-container-toolkit` (см. `docs/DEVELOPER.md` §11.2).
- [ ]  `nvidia-smi` работает на хосте.
- [ ]  `docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi` показывает GPU.
- [ ]  Свободного места ≥ 20 ГБ (`df -h /var/lib/docker`).
- [ ]  У тебя есть копия `.env` (вернёшь, если что).
- [ ]  Тестер/пользователи предупреждены о downtime.

### Шаг 1 — Бэкап Postgres

```bash
cd ~/projects/content-factory-console

# имя контейнера зависит от COMPOSE_PROJECT_NAME, проверь:
docker compose ps postgres

# бэкап:
docker compose exec -T postgres \
pg_dump -U app content_factory \
| gzip > ~/cfc_backup_$(date +%F).sql.gz

ls -lh ~/cfc_backup_*.sql.gz
# проверка целостности:
gunzip -t ~/cfc_backup_*.sql.gz && echo OK
```

### Шаг 2 — Архив PNG из ComfyUI/output (на хосте)

```bash
# путь должен совпадать с COMFY_OUTPUT_HOST из .env
tar czf ~/cfc_output_$(date +%F).tar.gz \
-C /path/to/ComfyUI output/

ls -lh ~/cfc_output_*.tar.gz
```

### Шаг 3 — Сохранить .env

```bash
cp .env ~/.env.r1.backup
```

### Шаг 4 — Остановить R1 БЕЗ удаления volumes

```bash
docker compose down
# ✅ КОРРЕКТНО — volumes (Postgres) остаются

# ❌ НЕ ДЕЛАТЬ:
# docker compose down -v   # ← снесёт Postgres со всеми job
```

### Шаг 5 — Остановить ComfyUI на хосте

```bash
# в терминале, где крутится ComfyUI
Ctrl+C
# или
pkill -f "python main.py.*8188"
```

### Шаг 6 — Переключиться на R2 ветку

```bash
git fetch --all --tags
git checkout main             # или release-2, если уже выделена
git pull
git log --oneline -5          # проверь, что ты на R2 коммите

# должны появиться:
ls scripts/preflight.py scripts/models_map.json scripts/Dockerfile.preflight
```

### Шаг 7 — Обновить `.env`

Открой `.env` и поменяй:

```bash
# Было (R1):
# COMFY_URL=http://host.docker.internal:8188
# COMFY_OUTPUT_HOST=/mnt/d/Development/ComfyUI_WSL/output

# Стало (R2):
COMFY_URL=http://comfyui:8188
# COMFY_OUTPUT_HOST больше не нужен — output в named volume
```

Остальные переменные (`POSTGRES_*`, `API_KEY`, `RATE_LIMIT_*`, `WORKER_*`) **не трогаем**.

```markdown
**Внимание!** Если вы в `.env` изменили `POSTGRES_PASSWORD`, а том `pg_data` остался от R1, то после запуска API не сможет подключиться к БД – пароль в томе не обновляется автоматически. Решение:
* либо используйте старый пароль в `.env` (как в R1),
* либо после поднятия R2 выполните:

```bash
>   docker compose exec -e PGPASSWORD=<старый_пароль> postgres psql -U app -d content_factory -c "ALTER USER app WITH PASSWORD '<новый_пароль>';"
```

### Шаг 8 — Поднять R2

```bash
docker compose up --build -d

# следим за preflight (скачивает SDXL, ~6.5 ГБ, 5–20 минут):
docker compose logs -f preflight
# дожидаемся: "preflight: all models ready"

# проверяем, что comfyui поднялся:
docker compose logs comfyui | tail -20
curl -sI http://localhost:8188/ | head -1   # → HTTP/1.1 200 OK
```

### Шаг 9 — Восстановить PNG в named volume

```bash
# имя volume: <project>_comfy_output
docker volume ls | grep comfy_output

# распаковываем архив прямо в volume через alpine‑контейнер:
docker run --rm \
-v content-factory-console_comfy_output:/dst \
-v ~:/src:ro \
alpine:3.19 \
sh -c 'cd /src && tar xzf cfc_output_*.tar.gz -C /dst --strip-components=1'

# проверка, что PNG появились в api:
docker compose exec api ls /comfy_output | head
```

### Шаг 10 — Smoke test

```bash
./scripts/smoke.sh
# должен пройти все 4 этапа: health → generate → polling → result → download
```

Или вручную:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/generate \
-H "Content-Type: application/json" \
-H "X-API-Key: $API_KEY" \
-d '{"prompt":"R2 smoke test, abstract","steps":15}'
# polling /jobs/{id}, потом /jobs/{id}/result, потом /files/{name}
```

### Шаг 11 — Поставить тег

```bash
git tag -a v2.0.0 -m "Release 2: ComfyUI in Docker with GPU passthrough"
git push origin v2.0.0
```

## Rollback (если R2 пошёл не так)

```bash
# 1. Останавливаем R2
cd ~/projects/content-factory-console
docker compose down

# 2. Возвращаемся на R1
git checkout v1.0.0

# 3. Восстанавливаем .env из бэкапа
cp ~/.env.r1.backup .env

# 4. Поднимаем R1
docker compose up -d --build

# 5. Запускаем ComfyUI на хосте
cd /path/to/ComfyUI
python main.py --listen 0.0.0.0 --port 8188 &

# 6. Если БД пострадала — restore
gunzip -c ~/cfc_backup_*.sql.gz \
| docker compose exec -T postgres psql -U app -d content_factory
```

# 7. Smoke test

```bash
./scripts/smoke.sh
```

## Параллельный запуск R1 и R2

### Вариант A — на одной машине (нужны разные порты)

Базовый R2 использует те же порты, что и R1 (`8000` для api, `8188` для comfyui). Чтобы развести:

1. **Скопируй проект в отдельную папку** для R2:

```bash
git clone git@github.com:Bogdan-95/content-factory-console.git ~/projects/content-factory-console-r2
cd ~/projects/content-factory-console-r2
git checkout release-2
```

2. **Создай отдельный `.env`** с другими портами:

```bash
COMPOSE_PROJECT_NAME=cfc-r2
```

3. **Поправь `docker-compose.yml`** в R2:

```yaml
api:
ports:
- "8001:8000"   # R1 на 8000, R2 на 8001
comfyui:
ports:
- "8189:8188"   # R1 на 8188, R2 на 8189
```

4. **Поднимай оба проекта**:

```bash
cd ~/projects/content-factory-console     && docker compose up -d   # R1 на 8000
cd ~/projects/content-factory-console-r2  && docker compose up -d   # R2 на 8001
```


БД у каждого своя (разные volumes из‑за разных `COMPOSE_PROJECT_NAME`).

### Вариант B — на разных машинах (рекомендованный)

- **Машина A:** R1 (`v1.0.0`), стабильная — для тестера / production / сравнительных бенчмарков.
- **Машина B:** R2 (`release-2` ветка) — активная разработка.
- БД у каждой своя — это не общая БД, не путать с репликацией.
- Для финального переключения: бэкап Postgres машины A → restore на машину B → DNS / прокси переключить → выключить машину A.

Это сценарий, который ты описывал: **«Тестер тестит R1, я разрабатываю R2».** Ничего не сломается, пока ты не сделаешь финальное переключение.