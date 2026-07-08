# tests/test_files_security.py
# Проверка защиты GET /files/{filename} от path traversal и плохих имён.

import pytest


@pytest.mark.parametrize(
    "bad",
    [
        "../ect/passwd",
        "..%2Fetc%2Fpasswd",
        "sub/dir/x.png",
        ".hidden",
        "",
    ],
)
def test_files_reject_traversal(client, bad):
    r = client.get(
        f"/files/{bad}",
        headers={"X-API-Key": "dev-local-key-change-me"},
    )
    assert r.status_code in (400, 404)
