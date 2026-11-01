# GET /jobs/{id}, /jobs/{id}/result

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_session
from ..schemas import JobOut, JobResultOut
from ..security import require_api_key
from ..services.jobs import get_job, get_result

router = APIRouter(tags=["jobs"], dependencies=[Depends(require_api_key)])


@router.get("/jobs/{job_id}", response_model=JobOut)
def job_status(
    job_id: int,
    db: Annotated[Session, Depends(get_session)],
) -> JobOut:
    """Получить статус задачи по ID."""
    row = get_job(db, job_id)
    if not row:
        raise HTTPException(status_code=404, detail="job not found")
    return JobOut(**row)


@router.get("/jobs/{job_id}/result", response_model=JobResultOut)
def job_result(
    job_id: int,
    db: Annotated[Session, Depends(get_session)],
) -> JobResultOut:
    """Получить результат генерации по ID задачи."""
    row = get_result(db, job_id)
    if not row:
        raise HTTPException(status_code=404, detail="result not ready")
    return JobResultOut(
        job_id=row["job_id"],
        filename=row["filename"],
        url=f"/files/{row['filename']}",
    )
