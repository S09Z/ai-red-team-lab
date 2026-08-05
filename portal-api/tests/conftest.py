"""Test fixtures for the portal API.

Each test gets an isolated SQLite database (in pytest's tmp_path) and a
``TestClient``. The stub login is enabled; cookies are non-Secure by default so
the sync test client round-trips them over plain HTTP.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Make the `app` package importable when pytest runs from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app  # noqa: E402
from app.settings import Settings  # noqa: E402


@pytest.fixture
def make_app(tmp_path):
    def _make(*, name: str = "test", **overrides):
        db = tmp_path / f"{name}.db"
        config = dict(
            database_url=f"sqlite+aiosqlite:///{db}",
            auth_stub=True,
            cookie_secure=False,
            portal_secret_key="test-secret",
            frontend_origin="http://localhost:5173",
        )
        config.update(overrides)
        return create_app(Settings(**config))

    return _make


@pytest.fixture
def client(make_app):
    with TestClient(make_app()) as c:
        yield c
