# tests/test_health.py
# Проверка эндпоинта проверки живости сервера.


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
