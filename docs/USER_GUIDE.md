# 📘 Руководство пользователя Content Factory Console

[![Release v2.0.0](https://img.shields.io/badge/release-v2.0.0-blue)](../CHANGELOG.md)

---

**Content Factory Console** — production‑ready API‑сервис для генерации изображений через Stable Diffusion XL + ComfyUI.  
Версия 2.0.0: всё работает в Docker, включая ComfyUI с GPU‑ускорением. Модели скачиваются автоматически. Достаточно одного `docker compose up`.

Разработчикам — см. [`docs/DEVELOPER.md`](./DEVELOPER.md).  
Миграция с версии 1 — [`docs/MIGRATION_R1_TO_R2.md`](./MIGRATION_R1_TO_R2.md).

---

## 📋 Требования

- **ОС:** Ubuntu 22.04+ / Windows 11 + WSL2 / macOS (на macOS GPU‑пасстр не работает в Docker — используйте нативную ComfyUI).
- **Docker:** Engine 24+ с плагином `docker compose` (или Docker Desktop).
- **RAM:** ≥ 16 ГБ.
- **Диск:** ≥ 50 ГБ свободного места (модели + выходные изображения).
- **GPU:** NVIDIA с 8+ ГБ VRAM (для генерации через ComfyUI; сам пульт работает без GPU).

### Дополнительно для Release 2

- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) (для проброса GPU в Docker).

---

## 🚀 Установка

### 1. Клонирование репозитория

```bash
git clone git@github.com:Bogdan-95/content-factory-console.git
cd content-factory-console
```

### 2. Создание файла конфигурации

```bash
cp .env.example .env
```

**Откройте .env в любом редакторе и задайте обязательные параметры:**

- `POSTGRES_PASSWORD` – придумайте пароль для БД.

- `API_KEY` – сгенерируйте ключ (например, openssl rand -hex 32). По умолчанию dev-local-key-change-me небезопасен.

- `ALLOWED_ORIGINS` – укажите адрес вашего фронтенда, если он есть.

- Остальные параметры можно оставить как есть.


**Release 2** 	В контейнере Docker	http://comfyui:8188
Для выбора достаточно раскомментировать нужную строку в `.env`.
Для `R1` также потребуется указать реальный путь `COMFY_OUTPUT_HOST`.

---
# ⚡ Запуск

### Release 2 (всё в Docker)

```bash
cd content-factory-console
docker compose up --build
```

### При первом запуске:

1. Поднимется `Postgres`.

2. Контейнер `preflight` скачает модель `SDXL Base (~6.5 ГБ)`. Это может занять 5–20 минут.

Когда появится сообщение `✅ preflight: all models ready`, запустится ComfyUI.

API станет доступно на `http://localhost:8000`.

Следить за прогрессом можно в логах: `docker compose logs -f preflight`.

---

## 📡 Использование API

Все запросы (кроме `/health`) требуют `HTTP‑заголовок X-API-Key` с вашим ключом.

#### Интерактивная документация доступна через Swagger UI:

👉 http://localhost:8000/docs

#### 1. Проверка работоспособности

```bash
curl http://localhost:8000/health
# {"ok": true}
```

### 1. Создание задания на генерацию

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key-change-me" \
  -d '{
    "prompt": "a cozy cabin in the snowy forest, volumetric light, 8k",
    "negative": "low quality, blurry",
    "width": 1024,
    "height": 1024,
    "steps": 25,
    "cfg": 7.5,
    "seed": -1
  }'
```

Пример ответа:

```json
{"job_id": 7, "status": "queued"}
```

#### Доступные поля генерации:

```makrdown
| Поле       | Тип    | Диапазон | По умолчанию  | Описание                                                |
| :--------- | :----- | :------: | :-----------: | :------------------------------------------------------ |
| `prompt`   | string |  1…2000  | *обязательно* | Положительный промпт                                    |
| `negative` | string |  0…2000  |     `""`      | Что исключить из изображения                            |
| `width`    | int    | 256…2048 |    `1024`     | Ширина в пикселях                                       |
| `height`   | int    | 256…2048 |    `1024`     | Высота в пикселях                                       |
| `steps`    | int    |   1…80   |     `20`      | Число шагов диффузии (больше = качественнее, но дольше) |
| `cfg`      | float  |   0…30   |     `7.0`     | CFG scale (соответствие промпту)                        |
| `seed`     | int    |   ≥ −1   |     `-1`      | Зерно случайности; −1 = случайное                       |
```

---

### 3. Проверка статуса задания

```bash
curl -H "X-API-Key: ваш_ключ" http://localhost:8000/jobs/1

```

#### Возможные статусы:

>[!NOTE]
- `queued` — ожидает обработки.
- `processing` — worker взял задание и отправляет на ComfyUI.
- `done` — генерация успешно завершена.
- `failed` — ошибка (см. поле error в ответе).


### 4. Получение имени файла и скачивание
Когда статус станет done, запросите ссылку на результат:

```bash
# получить имя файла
curl -H "X-API-Key: ваш_ключ" http://localhost:8000/jobs/1/result
# {"job_id":1,"filename":"ComfyUI_00001_.png","url":"/files/ComfyUI_00001_.png"}
```

#### Скачайте изображение:

```bash
curl -O http://localhost:8000/files/ComfyUI_00001_.png
```

### 5. Быстрый smoke‑тест
В репозитории есть готовый скрипт:

```bash
./scripts/smoke.sh
```

Он автоматически выполнит всю цепочку и сохранит сгенерированное изображение.

### 🔐 Безопасность
Все эндпоинты (кроме `/health`) закрыты API‑ключом.

Включён rate‑limit: после превышения `RATE_LIMIT_PER_MIN` запросов в минуту возвращается `429`.

CORS разрешает только указанные источники.

Контейнеры работают от непривилегированных пользователей.

Никогда не используйте ключ по умолчанию в production. Сгенерируйте новый при первом деплое и храните в защищённом месте.

---

#### 🧪 Примеры использования
**Простая генерация (минимальный запрос)**

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key-change-me" \
  -d '{"prompt":"a red apple on a wooden table"}'
```

**Фиксированный seed для воспроизводимости**

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key-change-me" \
  -d '{"prompt":"a cyberpunk street at night","seed":42,"steps":30}'
```

**Пакетная генерация (bash цикл)**

```bash
for prompt in "a cat astronaut" "a dog samurai" "a hamster wizard"; do
  curl -sX POST http://localhost:8000/generate \
    -H "Content-Type: application/json" \
    -H "X-API-Key: dev-local-key-change-me" \
    -d "{\"prompt\":\"$prompt\"}" &
done
# wait
# Worker обрабатывает задания по одному, поэтому они будут выполнены последовательно.
```

#### Полноценный Python‑клиент

```python
import time, requests

BASE = "http://localhost:8000"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "ваш_ключ"
}

# Создаём задание
r = requests.post(
    f"{BASE}/generate",
    headers=HEADERS,
    json={"prompt": "oil painting of a lighthouse at dusk", "steps": 25},
    timeout=10,
).json()
job_id = r["job_id"]
print(f"Job {job_id} created")

# Ожидаем завершения
while True:
    s = requests.get(f"{BASE}/jobs/{job_id}", headers=HEADERS).json()
    print(f"Status: {s['status']}")
    if s["status"] in ("done", "failed"):
        break
    time.sleep(2)

if s["status"] == "failed":
    print("Generation failed:", s.get("error"))
else:
    res = requests.get(f"{BASE}/jobs/{job_id}/result", headers=HEADERS).json()
    img = requests.get(f"{BASE}{res['url']}", headers=HEADERS).content
    with open(res["filename"], "wb") as f:
        f.write(img)
    print(f"Saved {res['filename']}")

```

>[!WARNING]

```markdown
❗ Частые проблемы и их решение
- **`api` не стартует** — проверь пароль Postgres в `.env` и доступность БД.
- **`403 invalid API key`** – не передан заголовок `X-API-Key` или ключ неверный.
- **`connection refused` к ComfyUI** — запущен ли он? Listen ли на `0.0.0.0`?
- **`429 Too Many Requests`** — включён rate‑limit. Увеличь `RATE_LIMIT_PER_MIN` в .`env`.
- **Долго генерирует** — нормально для SDXL на слабом GPU. Уменьши `steps` до 15–20.
- **GPU не виден (R2)** — проверь `nvidia-container-toolkit` и `nvidia-smi` через `--gpus all`.
```

---

## 🛑 Остановка и очистка

```bash
# Остановить контейнеры (сохраняя данные БД и сгенерированные файлы)
docker compose down

# Остановить и удалить все данные (volumes)
docker compose down -v

```

## 📚 Дополнительная документация
Swagger UI: `http://localhost:8000/docs`

ComfyUI (GUI): `http://localhost:8188` (если нужен прямой доступ к интерфейсу)

README: `README.md`