# POST /generate

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_session
from ..schemas import GenerateIn, GenerateOut
from ..services.jobs import create_job

router = APIRouter(tags=["generate"])


@router.post("/generate", response_model=GenerateOut, status_code=202)
def generate(data: GenerateIn, db: Session = Depends(get_session)) -> GenerateOut:
    """Поставить задачу в очередь на генерацию."""
    job_id = create_job(db, data)
    return GenerateOut(job_id=job_id, status="queued")
