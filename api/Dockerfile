# api/Dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# deps
COPY requirements.txt .
RUN pip install -r requirements.txt

# code 
COPY app ./app

# non-root user // TODO: см. раздел «Перед продакшеном»
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# dev: один uvicorn. В проде — gunicorn с UvicornWorker (см. прод-раздел).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]