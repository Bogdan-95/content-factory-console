# GET /jobs/{id}, /jobs/{id}/result

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_session
from ..schemas import JobOut, JobResultOut
from ..services.jobs import get_job, get_result

# Создаём роутер с тегом "jobs" — группирует эндпоинты в Swagger-документации
router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobOut)
def job_status(job_id: int, db: Session = Depends(get_session)) -> JobOut:
    """
    Получить статус задачи по её ID.
    Возвращает:
    - 200 + JobOut (статус, тайминги, ошибка — если failed)
    - 404 — если задача не найдена"""
    row = get_job(db, job_id)
    if not row:
        raise HTTPException(status_code=404, detail="job not found")
    return JobOut(**row)


@router.get("/jobs/{job_id}/result", response_model=JobResultOut)
def job_result(job_id: int, db: Session = Depends(get_session)) -> JobResultOut:
    """Получить результат генерации (ссылку на файл) по ID задачи.
    Возвращает:
    - 200 + JobResultOut (job_id, filename, url для скачивания)
    - 404 — если результат ещё не готов (задача в очереди или processing)"""
    row = get_result(db, job_id)
    if not row:
        raise HTTPException(status_code=404, detail="result not ready")
    return JobResultOut(
        job_id=row["job_id"],
        filename=row["filename"],
        url=f"/files/{row['filename']}",
    )
