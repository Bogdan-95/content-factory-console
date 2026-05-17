#!/usr/bin/env bash
# Smoke‑тест (быстрая проверка работоспособности) для Content Factory Console.

set -euo pipefail
BASE=${BASE:-http://localhost:8000}
API_KEY=${API_KEY:-dev-local-key-change-me}

# Шаг 1/4: Проверка живости API
echo "[1/4] /health"
curl -fsS "$BASE/health" ; echo

# Шаг 2/4: Создание задачи на генерацию
echo "[2/4] POST /generate"
JOB=$(curl -fsS -X POST "$BASE/generate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"prompt":"smoke test, abstract geometric shapes","steps":10}' \
  | python -c 'import sys,json; print(json.load(sys.stdin)["job_id"])')
echo "job_id=$JOB"

# Шаг 3/4: Ожидание завершения задачи
echo "[3/4] polling"
for i in $(seq 1 120); do
  STATUS=$(curl -fsS "$BASE/jobs/$JOB" | python -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  echo "  t=$i status=$STATUS"
  [[ "$STATUS" == "done" ]] && break
  [[ "$STATUS" == "failed" ]] && { echo FAILED ; exit 1 ; }
  sleep 2
done

# Шаг 4/4: Получение результата и скачивание файла
echo "[4/4] /jobs/$JOB/result"
NAME=$(curl -fsS "$BASE/jobs/$JOB/result" | python -c 'import sys,json; print(json.load(sys.stdin)["filename"])')
echo "filename=$NAME"
curl -fsS -o "$NAME" "$BASE/files/$NAME"
echo "saved $NAME ($(wc -c <"$NAME") bytes)"