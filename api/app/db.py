# SQLAlchemy engine + session

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .settings import settings

# Engine - Подключение к БД
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    future=True,
)

# SessionLocal — фабрика сессий (по одной на запрос)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Session:
    """FastAPI dependency: выдаёт Session и закрывает её после запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
