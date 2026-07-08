# интеграционный: SKIP LOCKED

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker


def test_pick_one_skips_locked(client, db_engine, worker_engine):
    # Создаём задачи через API (с ключом)
    client.post(
        "/generate",
        json={"prompt": "p1"},
        headers={"X-API-Key": "dev-local-key-change-me"},
    )
    client.post(
        "/generate",
        json={"prompt": "p2"},
        headers={"X-API-Key": "dev-local-key-change-me"},
    )

    TestSession = sessionmaker(bind=worker_engine)

    # Первая сессия блокирует первую задачу и НЕ завершает транзакцию
    s1 = TestSession()
    locked_id = s1.execute(
        text("SELECT id FROM jobs WHERE status='queued' LIMIT 1 FOR UPDATE")
    ).scalar_one()
    # не делаем commit() – блокировка удерживается

    # Вторая сессия должна пропустить заблокированную строку
    s2 = TestSession()
    picked_id = s2.execute(
        text("SELECT id FROM jobs WHERE status='queued' LIMIT 1 FOR UPDATE SKIP LOCKED")
    ).scalar_one()
    s2.commit()
    s2.close()

    # Теперь можно завершить первую транзакцию
    s1.commit()
    s1.close()

    assert picked_id != locked_id, (
        f"SKIP LOCKED не сработало: заблокированная и взятая задачи совпадают ({picked_id})"
    )
