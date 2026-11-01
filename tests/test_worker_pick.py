"""Integration test for the actual worker pickup function and SKIP LOCKED."""

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker


def test_pick_one_skips_locked_job(client, db_engine, worker_session):
    headers = {"X-API-Key": "dev-local-key-change-me"}
    first = client.post("/generate", json={"prompt": "first"}, headers=headers)
    second = client.post("/generate", json={"prompt": "second"}, headers=headers)

    assert first.status_code == 202
    assert second.status_code == 202

    test_sessions = sessionmaker(bind=db_engine, autoflush=False, future=True)
    lock_session = test_sessions()

    try:
        locked_id = lock_session.execute(
            text(
                """
                SELECT id
                FROM jobs
                WHERE status = 'queued'
                ORDER BY created_at, id
                LIMIT 1
                FOR UPDATE
                """
            )
        ).scalar_one()

        picked = worker_session.pick_one()

        assert picked is not None
        assert picked["id"] != locked_id

        with db_engine.connect() as connection:
            picked_status = connection.execute(
                text("SELECT status FROM jobs WHERE id = :job_id"),
                {"job_id": picked["id"]},
            ).scalar_one()

        assert picked_status == "processing"
    finally:
        lock_session.rollback()
        lock_session.close()
