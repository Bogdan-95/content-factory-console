# Pydantic: вход/выход API

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GenerateIn(BaseModel):
    """Схема запроса."""

    prompt: str = Field(..., min_length=1, max_length=2000)
    negative: str = Field("", max_length=2000)
    width: int = Field(1024, ge=256, le=2048)
    height: int = Field(1024, ge=256, le=2048)
    steps: int = Field(20, ge=1, le=80)
    cfg: float = Field(7.0, ge=0, le=30)
    seed: int = Field(-1, ge=-1)


class GenerateOut(BaseModel):
    """Схема ответа на POST."""

    job_id: int
    status: Literal["queued"]


class JobOut(BaseModel):
    """Схема ответа на GET."""

    id: int
    status: Literal["queued", "processing", "done", "failed"]
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


class JobResultOut(BaseModel):
    """Схема ответа на GET /jobs/:job_id/result."""

    job_id: int
    filename: str
    url: str
