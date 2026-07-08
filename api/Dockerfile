# api/Dockerfile - продакшен-образ FastAPI
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# deps
COPY api/requirements.txt .
RUN pip install -r requirements.txt

# code 
COPY api/app ./app

# Alembic - configuration and migration
COPY alembic.ini .
COPY migrations_alembic ./migrations_alembic

# Pre-launch migration script
COPY api/prestart.sh .
RUN chmod +x prestart.sh

# Unprivileged user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

ENTRYPOINT ["./prestart.sh"]

# Production: gunicorn + UvicornWorker (4 воркера – подберите под CPU)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", \
    "--workers", "4", "--bind", "0.0.0.0:8000", \
    "--access-logfile", "-", "--error-logfile", "-", \
    "app.main:app"]