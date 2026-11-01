"""Shared, isolated PostgreSQL fixtures for API and worker tests."""

import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from api.app.main import app

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://test:test@localhost:5432/test",
)


def _validate_test_database(url: str) -> None:
    parsed = make_url(url)
    allowed_hosts = {"localhost", "127.0.0.1", "::1", "postgres"}

    if parsed.database != "test":
        raise RuntimeError(
            "Refusing to reset database: TEST_DATABASE_URL must target a database named 'test'."
        )
    if parsed.host not in allowed_hosts:
        raise RuntimeError(
            "Refusing to reset database: TEST_DATABASE_URL must point to a local test host."
        )


@pytest.fixture(scope="session")
def db_engine():
    """Create the isolated test schema using the project's Alembic migrations."""
    _validate_test_database(TEST_DB_URL)
    engine = create_engine(TEST_DB_URL, future=True)

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(db_engine):
    """Keep tests independent without dropping the migration-managed schema."""
    with db_engine.begin() as connection:
        connection.execute(
            text("TRUNCATE TABLE job_results, jobs RESTART IDENTITY CASCADE")
        )


@pytest.fixture
def client(db_engine, monkeypatch):
    """Route API database access to the guarded test database."""
    import api.app.db as api_db

    test_sessions = sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )
    monkeypatch.setattr(api_db, "engine", db_engine)
    monkeypatch.setattr(api_db, "SessionLocal", test_sessions)

    return TestClient(app)


@pytest.fixture
def worker_session(db_engine, monkeypatch):
    """Patch the SessionLocal reference used by the worker module."""
    import worker.app.worker as worker

    test_sessions = sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )
    monkeypatch.setattr(worker, "SessionLocal", test_sessions)
    return worker
