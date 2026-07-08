# tests/test_generate.py
# Тесты для POST /generate — создание задачи на генерацию.
# Проверяем успешное создание и валидацию входных данных.


def test_generate_creates_queued_job(client, db_engine):
    # Шаг 1: POST /generate — создать новую задачу
    r = client.post(
        "/generate",
        json={"prompt": "a cat"},
        headers={"X-API-Key": "dev-local-key-change-me"},
    )
    assert r.status_code == 202, f"Expected 202, got {r.status_code}"
    body = r.json()
    assert body["status"] == "queued", f"Expected status 'queued', got {body['status']}"
    assert isinstance(body["job_id"], int), (
        f"job_id should be int, got {type(body['job_id'])}"
    )

    # Шаг 2: GET /jobs/{job_id} — получить текущий статус задачи
    r2 = client.get(
        f"/jobs/{body['job_id']}",
        headers={"X-API-Key": "dev-local-key-change-me"},
    )
    assert r2.status_code == 200, f"Expected 200, got {r2.status_code}"
    assert r2.json()["status"] == "queued", (
        f"Expected status 'queued', got {r2.json()['status']}"
    )


def test_generate_validation(client):
    """Проверяет валидацию входных данных."""
    r = client.post(
        "/generate",
        json={"prompt": ""},
        headers={"X-API-Key": "dev-local-key-change-me"},
    )
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    detail = r.json().get("detail")
    assert detail is not None, "Validation error should contain 'detail'"
