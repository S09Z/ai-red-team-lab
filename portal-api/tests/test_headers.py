"""Portal responses carry the 9 security headers and a hardened session cookie."""

from __future__ import annotations

from app.security import SECURITY_HEADERS
from fastapi.testclient import TestClient


def test_all_nine_security_headers_present(client):
    resp = client.get("/health")
    for name in SECURITY_HEADERS:
        assert name in resp.headers, f"missing {name}"


def test_session_cookie_is_httponly_and_samesite(client):
    resp = client.post("/auth/stub")
    set_cookie = resp.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie


def test_session_cookie_secure_flag_when_enabled(make_app):
    with TestClient(make_app(name="secure", cookie_secure=True)) as c:
        set_cookie = c.post("/auth/stub").headers.get("set-cookie", "").lower()
        assert "secure" in set_cookie
