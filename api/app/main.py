# Точка входа FastAPI-приложения.
# Собирает всё воедино: lifespan, middlewares, rate-limit, роутеры.

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from .settings import settings
from .security import limiter
from .routers import health, generate, jobs, files

# Lifespan — асинхронный контекстный менеджер жизненного цикла приложения.


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Управляет ресурсами приложения на всём протяжении его жизни.
    """
    yield


# Создание экземпляра FastAPI
app = FastAPI(title="Content Factory Console", version="1.0.0", lifespan=lifespan)

# limiter создан в security.py с key_func=get_remote_address (считает по IP).
app.state.limiter = limiter

# RateLimitExceeded. Этот handler превращает его в HTTP 429 Too Many Requests
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

#    TODO:     # НИКОГДА не ставьте ["*"] в проде — это дыра в безопасности.

# CORS — Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Роутеры — подключаем все эндпоинт
app.include_router(health.router)  # GET /health проверка здоровья
app.include_router(generate.router)  # POST /generate создать задачу
app.include_router(jobs.router)  # GET /jobs/{id}/result — результат
app.include_router(files.router)  # GET /files/{name} — скачать PNG
