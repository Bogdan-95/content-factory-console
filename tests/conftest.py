# фикстуры: testdb, testclient

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from api.app.main import app

from api.app.db import engine as prod_engine

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://test:test@localhost:5432/test",
)


# Фикстура engine для тестов
@pytest.fixture(scope="session")
def db_engine():
    """Создает engine для тестовой БД"""
    e = create_engine(TEST_DB_URL, future=True)
    # открываем транзакцию и накатываем чистую схему
    with e.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS job_results, jobs CASCADE"))
        conn.execute(text("DROP TYPE IF EXISTS job_status"))

        # Читаем нашу миграцию и выполняем её — создаём таблицы заново
        with open("migrations/001_init.sql", "r", encoding="utf-8") as f:
            conn.execute(text(f.read()))
    return e


# Фикстура test-клиента
@pytest.fixture
def client(db_engine, monkeypatch):
    """Создаёт экземпляр TestClient, который будет слать запросы в FastAPI-приложение"""
    monkeypatch.setattr(prod_engine, "url", db_engine.url, raising=False)
    return TestClient(app)
