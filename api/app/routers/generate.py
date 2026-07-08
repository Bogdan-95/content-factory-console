# POST /generate

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..db import get_session
from ..schemas import GenerateIn, GenerateOut
from ..services.jobs import create_job
from ..security import limiter, require_api_key
from ..settings import settings

router = APIRouter(tags=["generate"], dependencies=[Depends(require_api_key)])


@router.post("/generate", response_model=GenerateOut, status_code=202)
@limiter.limit(lambda: f"{settings.rate_limit_per_min}/minute")
def generate(
    request: Request, data: GenerateIn, db: Session = Depends(get_session)
) -> GenerateOut:
    """Поставить задачу в очередь на генерацию."""
    job_id = create_job(db, data)
    return GenerateOut(job_id=job_id, status="queued")
