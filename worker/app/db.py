# SQLAlchemy engine + session (worker-side)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .settings import settings

# Engine — подключение к PostgreSQL (та же БД, что у API).
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

# SessionLocal — фабрика сессий.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
