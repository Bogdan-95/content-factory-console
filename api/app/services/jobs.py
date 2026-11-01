# CRUD-сервис: создать job, прочитать job/result

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..schemas import GenerateIn


def create_job(db: Session, data: GenerateIn) -> int:
    """Создать задачу в очереди и вернуть ID."""
    row = db.execute(
        text("""
            INSERT INTO jobs (prompt, negative, width, height, steps, cfg, seed)
            VALUES (:prompt, :negative, :width, :height, :steps, :cfg, :seed)
            RETURNING id
        """),
        data.model_dump(),
    ).scalar_one()
    db.commit()
    return int(row)


def get_job(db: Session, job_id: int) -> dict | None:
    """Получить задачу по ID или вернуть None."""
    row = (
        db.execute(
            text(
                "SELECT id, status, created_at, started_at, finished_at, error "
                "FROM jobs WHERE id = :id"
            ),
            {"id": job_id},
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


def get_result(db: Session, job_id: int) -> dict | None:
    """Получить результат генерации или вернуть None, если он ещё не готов."""
    row = (
        db.execute(
            text("SELECT job_id, filename FROM job_results WHERE job_id = :id"),
            {"id": job_id},
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None
