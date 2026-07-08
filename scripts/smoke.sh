#!/usr/bin/env bash
# Smoke-тест Content Factory Console – проверка полного цикла генерации
set -euo pipefail

# ---------- настройки ----------
BASE="${BASE_URL:-http://localhost:8000}"
KEY="${API_KEY:-dev-local-key-change-me}"
COLOUR_GREEN='\033[0;32m'
COLOUR_RED='\033[0;31m'
COLOUR_RESET='\033[0m'

# ---------- проверка на dev-ключ ----------
if [ "$KEY" = "dev-local-key-change-me" ]; then
  echo -e "${COLOUR_RED}⚠️  ВНИМАНИЕ: используется API-ключ по умолчанию.
  ${COLOUR_RESET}"
fi

# ---------- шаг 1: health ----------
echo -e "\n========================================"
echo " Шаг 1/4: Проверка здоровья сервиса (health)"
echo "========================================"
if HEALTH=$(curl -fsS "$BASE/health" 2>&1); then
  echo -e "✅ Сервис доступен: $HEALTH"
else
  echo -e "${COLOUR_RED}❌ Ошибка: сервис не отвечает. Проверьте запущен ли docker compose и порт $BASE${COLOUR_RESET}"
  exit 1
fi

# ---------- шаг 2: создание задачи ----------
echo -e "\n========================================"
echo " Шаг 2/4: Создание задачи (POST /generate)"
echo "========================================"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/generate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $KEY" \
  -d '{
    "prompt": "professional portrait of a beautiful Egyptian woman with perfect natural skin texture, detailed facial features, soft sunlight, golden hour, photorealistic, 8k, shot on Canon EOS R5, 85mm f/1.2",
    "negative": "bad anatomy, blurry, distorted, deformed, ugly, plastic skin, cartoon, painting",
    "steps": 25,
    "cfg": 7.5
  }')
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

if [ "$HTTP_CODE" -ne 202 ]; then
  echo -e "${COLOUR_RED}❌ Ошибка при создании задачи (HTTP $HTTP_CODE). Ответ сервера:${COLOUR_RESET}"
  echo "$BODY"
  exit 1
fi

echo "Ответ: $BODY"

# извлекаем job_id
if ! JOB_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null); then
  echo -e "${COLOUR_RED}❌ Не удалось получить job_id из ответа. Возможно, сервер вернул ошибку.${COLOUR_RESET}"
  exit 1
fi
echo -e "✅ Задача зарегистрирована. ID задачи: $JOB_ID"

# ---------- шаг 3: ожидание завершения ----------
echo -e "\n========================================"
echo " Шаг 3/4: Ожидание завершения генерации"
echo "========================================"
echo "Опрос статуса каждые 2 секунды (максимум 60 попыток)..."

MAX_TRIES=60
for i in $(seq 1 $MAX_TRIES); do
  STATUS_RESP=$(curl -s "$BASE/jobs/$JOB_ID" -H "X-API-Key: $KEY")
  STATUS=$(echo "$STATUS_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")
  echo "  [$i/$MAX_TRIES] Статус: $STATUS"

  if [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done

if [ "$STATUS" = "failed" ]; then
  ERROR_MSG=$(echo "$STATUS_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error','неизвестная ошибка'))" 2>/dev/null || echo "неизвестная ошибка")
  echo -e "${COLOUR_RED}❌ Задача завершилась с ошибкой: $ERROR_MSG${COLOUR_RESET}"
  exit 1
elif [ "$STATUS" != "done" ]; then
  echo -e "${COLOUR_RED}❌ Превышено время ожидания (${MAX_TRIES} попыток). Задача не завершена.${COLOUR_RESET}"
  exit 1
fi

echo -e "✅ Генерация успешно завершена."

# ---------- шаг 4: получение результата и скачивание ----------
echo -e "\n========================================"
echo " Шаг 4/4: Получение и сохранение результата"
echo "========================================"
RESULT=$(curl -s "$BASE/jobs/$JOB_ID/result" -H "X-API-Key: $KEY")
echo "Ответ: $RESULT"

FILENAME=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['filename'])" 2>/dev/null || echo "")
if [ -z "$FILENAME" ]; then
  echo -e "${COLOUR_RED}❌ Имя файла не найдено в ответе.${COLOUR_RESET}"
  exit 1
fi

DOWNLOAD_NAME="smoke_${FILENAME}"
if curl -f -s -o "$DOWNLOAD_NAME" "$BASE/files/$FILENAME" -H "X-API-Key: $KEY"; then
  echo "Скачан файл: $DOWNLOAD_NAME"
else
  echo -e "${COLOUR_RED}❌ Не удалось скачать файл.${COLOUR_RESET}"
  exit 1
fi

FILETYPE=$(file "$DOWNLOAD_NAME")
if echo "$FILETYPE" | grep -qi "PNG"; then
  echo -e "✅ Тип файла: PNG изображение"
else
  echo -e "${COLOUR_RED}❌ Полученный файл не является PNG: $FILETYPE${COLOUR_RESET}"
  exit 1
fi

SIZE=$(wc -c < "$DOWNLOAD_NAME" | tr -d ' ')
echo -e "\n========================================"
echo -e " ✅ Тест успешно пройден!"
echo -e " Сгенерированное изображение: $DOWNLOAD_NAME ($SIZE байт)"
echo -e "========================================"