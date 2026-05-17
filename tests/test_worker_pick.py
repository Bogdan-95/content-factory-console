# интеграционный: SKIP LOCKED
from sqlalchemy import text
from worker.app.worker import pick_one
from worker.app.db import SessionLocal as WorkerSession


def test_pick_one_skips_locked(client, db_engine):
    client.post("/generate", json={"prompt": "p1"})
    client.post("/generate", json={"prompt": "p2"})

    with WorkerSession() as s:
        s.execute(
            text("SELECT id FROM jobs WHERE status='queued' LIMIT 1 FOR UPDATE")
        ).first()
        picked = pick_one()
        assert picked is not None
