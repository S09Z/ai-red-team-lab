"""Stub-login auth flow: cookie issuance, /me, logout, and OAuth gating."""

from __future__ import annotations


def test_stub_login_issues_cookie_and_me_returns_user(client):
    resp = client.post("/auth/stub")
    assert resp.status_code == 200
    assert resp.json()["email"] == "dev@lab.local"
    assert "portal_session" in resp.cookies

    me = client.get("/me")
    assert me.status_code == 200
    assert me.json()["email"] == "dev@lab.local"
    # /me exposes no sensitive fields.
    assert "provider_sub" not in me.json()


def test_me_requires_authentication(client):
    assert client.get("/me").status_code == 401


def test_logout_clears_session(client):
    client.post("/auth/stub")
    assert client.get("/me").status_code == 200
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/me").status_code == 401


def test_stub_disabled_returns_404(make_app):
    from fastapi.testclient import TestClient

    with TestClient(make_app(name="nostub", auth_stub=False)) as c:
        assert c.post("/auth/stub").status_code == 404


def test_unconfigured_oauth_provider_returns_503(client):
    # No GitHub/Google secrets in the test settings -> provider not registered.
    assert client.get("/auth/github/login").status_code == 503
    assert client.get("/auth/google/login").status_code == 503


def test_unknown_provider_returns_404(client):
    assert client.get("/auth/twitter/login").status_code == 404
