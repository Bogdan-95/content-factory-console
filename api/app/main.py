# Точка входа FastAPI-приложения для Content Factory Console.
# Содержит lifespan, middlewares (CORS, rate-limit), подключение роутеров.

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from .settings import settings
from .security import limiter
from .routers import health, generate, jobs, files

log = logging.getLogger("api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info("Starting up API...")
    yield
    log.info("Shutting down API...")


app = FastAPI(
    title="Content Factory Console",
    version="2.0.0",
    lifespan=lifespan,
)

# Rate limiter (in-memory, keyed by client IP)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

# CORS — разрешённые источники из .env
origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(health.router)  # GET /health
app.include_router(generate.router)  # POST /generate
app.include_router(jobs.router)  # GET /jobs/{id}, /jobs/{id}/result
app.include_router(files.router)  # GET /files/{name}
