"""Regression tests for worker job-state guards."""

import pytest
from sqlalchemy import text


def _create_job(db_engine, status: str) -> int:
    with db_engine.begin() as connection:
        return connection.execute(
            text(
                "INSERT INTO jobs (prompt, status) "
                "VALUES (:prompt, CAST(:status AS job_status)) RETURNING id"
            ),
            {"prompt": f"test job in {status}", "status": status},
        ).scalar_one()


def _job_state(db_engine, job_id: int) -> dict:
    with db_engine.connect() as connection:
        return dict(
            connection.execute(
                text(
                    "SELECT status, comfy_prompt_id, error "
                    "FROM jobs WHERE id = :id"
                ),
                {"id": job_id},
            )
            .mappings()
            .one()
        )


def _result_count(db_engine, job_id: int) -> int:
    with db_engine.connect() as connection:
        return connection.execute(
            text("SELECT count(*) FROM job_results WHERE job_id = :id"),
            {"id": job_id},
        ).scalar_one()


@pytest.mark.parametrize(
    ("status", "expected_saved"),
    [
        ("processing", True),
        ("queued", False),
        ("done", False),
        ("failed", False),
    ],
)
def test_save_prompt_id_only_updates_processing_jobs(
    db_engine, worker_session, status, expected_saved
):
    job_id = _create_job(db_engine, status)

    saved = worker_session.save_prompt_id(job_id, "comfy-prompt-123")

    assert saved is expected_saved
    state = _job_state(db_engine, job_id)
    assert state["status"] == status
    assert state["comfy_prompt_id"] == ("comfy-prompt-123" if expected_saved else None)


@pytest.mark.parametrize("status", ["queued", "done", "failed"])
def test_mark_done_does_not_overwrite_non_processing_jobs(
    db_engine, worker_session, status
):
    job_id = _create_job(db_engine, status)

    worker_session.mark_done(job_id, "comfy-prompt-456", "result.png")

    assert _job_state(db_engine, job_id)["status"] == status
    assert _result_count(db_engine, job_id) == 0


@pytest.mark.parametrize("status", ["queued", "done", "failed"])
def test_mark_failed_does_not_overwrite_non_processing_jobs(
    db_engine, worker_session, status
):
    job_id = _create_job(db_engine, status)

    worker_session.mark_failed(job_id, "late worker error")

    state = _job_state(db_engine, job_id)
    assert state["status"] == status
    assert state["error"] is None


def test_mark_done_updates_processing_job_and_inserts_result_once(
    db_engine, worker_session
):
    job_id = _create_job(db_engine, "processing")

    worker_session.mark_done(job_id, "comfy-prompt-789", "result.png")

    state = _job_state(db_engine, job_id)
    assert state["status"] == "done"
    assert state["comfy_prompt_id"] == "comfy-prompt-789"
    assert _result_count(db_engine, job_id) == 1


def test_mark_failed_updates_processing_job(db_engine, worker_session):
    job_id = _create_job(db_engine, "processing")

    worker_session.mark_failed(job_id, "ComfyUI failed")

    state = _job_state(db_engine, job_id)
    assert state["status"] == "failed"
    assert state["error"] == "ComfyUI failed"
