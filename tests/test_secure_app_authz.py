"""Authorization / injection fixes on the hardened target.

Each test asserts that a flaw present in ``targets/flask-app`` is closed in
``targets/flask-app-secure``: SQLi login bypass, IDOR, open redirect,
sensitive-data exposure, the removed ``/debug`` dump, and the weak-JWT fix.
"""

import sys
from pathlib import Path

import jwt
import pytest

SECURE_APP_DIR = Path(__file__).resolve().parents[1] / "targets" / "flask-app-secure"
sys.path.insert(0, str(SECURE_APP_DIR))

from app import create_app  # noqa: E402


@pytest.fixture
def app(tmp_path):
    return create_app(testing=True, database=str(tmp_path / "secure.db"))


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client, username, password):
    return client.post(
        "/login", data={"username": username, "password": password}
    )


def test_sqli_login_bypass_rejected(client):
    resp = _login(client, "admin'--", "anything")

    # No redirect to /dashboard; the classic SQLi payload is now inert.
    assert resp.status_code == 200
    assert b"Invalid credentials" in resp.data


def test_valid_login_succeeds(client):
    resp = _login(client, "admin", "admin123")

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/dashboard")


def test_idor_profile_update_blocked(client):
    _login(client, "alice", "password")  # alice is user id 2

    resp = client.post("/profile/1/update", data={"bio": "hacked"})

    assert resp.status_code == 403


def test_open_redirect_external_rejected(client):
    resp = client.get("/redirect?next=http://evil.example.com/phish")

    assert resp.status_code == 302
    assert "evil.example.com" not in resp.headers["Location"]


def test_open_redirect_relative_allowed(client):
    resp = client.get("/redirect?next=/dashboard")

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/dashboard")


def test_api_users_requires_auth(client):
    assert client.get("/api/users").status_code == 401


def test_api_users_exposes_no_password(client):
    _login(client, "admin", "admin123")
    data = client.get("/api/users").get_json()

    assert data
    for row in data:
        assert "password" not in row
        assert "password_hash" not in row
        assert "email" not in row


def test_debug_endpoint_removed(client):
    assert client.get("/debug").status_code == 404


def test_jwt_has_expiry_and_no_admin_claim(client):
    resp = client.post(
        "/api/token", json={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 200
    token = resp.get_json()["token"]

    claims = jwt.decode(token, options={"verify_signature": False})
    assert "exp" in claims
    assert claims["sub"] == "admin"
    # is_admin must NOT be embedded — callers re-check against the DB.
    assert "is_admin" not in claims


def test_jwt_wrong_password_rejected(client):
    resp = client.post(
        "/api/token", json={"username": "admin", "password": "wrong"}
    )

    assert resp.status_code == 401


def test_csrf_enforced_when_enabled(tmp_path):
    # A non-testing app has CSRF protection on; a POST without a token is 400.
    app = create_app(testing=False, database=str(tmp_path / "csrf.db"))
    client = app.test_client()

    resp = client.post("/login", data={"username": "admin", "password": "admin123"})

    assert resp.status_code == 400
