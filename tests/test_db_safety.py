"""Safety checks for the destructive integration-test database setup."""

import pytest

from tests.conftest import _validate_test_database


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://user:pass@localhost:5432/production",
        "postgresql+psycopg://user:pass@db.example.com:5432/test",
    ],
)
def test_rejects_non_test_or_remote_database(url):
    with pytest.raises(RuntimeError, match="Refusing to reset database"):
        _validate_test_database(url)


def test_accepts_local_test_database():
    _validate_test_database("postgresql+psycopg://test:test@127.0.0.1:5432/test")
