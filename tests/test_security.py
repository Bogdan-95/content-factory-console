"""Regression tests for API-key fail-closed behavior."""

import pytest

from api.app import security


@pytest.mark.parametrize("header_value", ["incorrect-key", ""])
def test_generate_rejects_invalid_or_empty_api_key(client, monkeypatch, header_value):
    monkeypatch.setattr(security.settings, "api_key", "configured-test-key")

    response = client.get(
        "/jobs/1",
        headers={"X-API-Key": header_value},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "invalid API key"}


def test_generate_rejects_requests_when_configured_api_key_is_empty(
    client, monkeypatch
):
    monkeypatch.setattr(security.settings, "api_key", "")

    response = client.get(
        "/jobs/1",
        headers={"X-API-Key": "configured-test-key"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "invalid API key"}
