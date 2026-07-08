# tests/conftest.py – фикстуры: testdb, testclient

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from api.app.main import app

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://test:test@localhost:5432/test",
)


@pytest.fixture(scope="session")
def db_engine():
    """Создаёт engine для тестовой БД и накатывает схему."""
    e = create_engine(TEST_DB_URL, future=True)

    # Удаляем старые таблицы, если есть
    with e.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS job_results, jobs CASCADE"))
        conn.execute(text("DROP TYPE IF EXISTS job_status CASCADE"))

    # Создаём схему напрямую (копия из 66a1a1ca5e9d_initial.py)
    with e.begin() as conn:
        conn.execute(
            text("""
            CREATE TYPE job_status AS ENUM ('queued', 'processing', 'done', 'failed');

            CREATE TABLE jobs (
                id            BIGSERIAL PRIMARY KEY,
                prompt        TEXT        NOT NULL,
                negative      TEXT        NOT NULL DEFAULT '',
                width         INT         NOT NULL DEFAULT 1024,
                height        INT         NOT NULL DEFAULT 1024,
                steps         INT         NOT NULL DEFAULT 20,
                cfg           REAL        NOT NULL DEFAULT 7.0,
                seed          BIGINT      NOT NULL DEFAULT -1,
                status        job_status  NOT NULL DEFAULT 'queued',
                error         TEXT,
                comfy_prompt_id TEXT,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
                started_at    TIMESTAMPTZ,
                finished_at   TIMESTAMPTZ
            );

            CREATE INDEX idx_jobs_status_created ON jobs (status, created_at);

            CREATE TABLE job_results (
                job_id     BIGINT PRIMARY KEY REFERENCES jobs (id) ON DELETE CASCADE,
                filename   TEXT     NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)
        )

    yield e

    # Очистка после всех тестов
    with e.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS job_results, jobs CASCADE"))
        conn.execute(text("DROP TYPE IF EXISTS job_status CASCADE"))
    e.dispose()


@pytest.fixture
def client(db_engine, monkeypatch):
    """Создаёт TestClient, полностью переключая API на тестовую БД."""
    import api.app.db as api_db

    monkeypatch.setattr(api_db, "engine", db_engine)

    TestSessionLocal = sessionmaker(
        bind=db_engine, autoflush=False, autocommit=False, future=True
    )
    monkeypatch.setattr(api_db, "SessionLocal", TestSessionLocal)

    return TestClient(app)


@pytest.fixture
def worker_engine(db_engine, monkeypatch):
    """Подменяет движок и сессии Worker на тестовые."""
    import worker.app.db as worker_db

    monkeypatch.setattr(worker_db, "engine", db_engine)
    TestSessionLocal = sessionmaker(
        bind=db_engine, autoflush=False, autocommit=False, future=True
    )
    monkeypatch.setattr(worker_db, "SessionLocal", TestSessionLocal)
    return db_engine
