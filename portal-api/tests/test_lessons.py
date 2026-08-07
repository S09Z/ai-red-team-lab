"""Lessons API: content, per-user progress, RBAC gating, and safe probe shape."""

from __future__ import annotations

import app.lessons as lessons_mod


def _login(c, *, email=None, role=None):
    body = {}
    if email:
        body["email"] = email
    if role:
        body["role"] = role
    return c.post("/auth/stub", json=body or None)


def test_list_and_detail(clients):
    admin = clients()
    _login(admin)

    lessons = admin.get("/api/lessons").json()
    assert len(lessons) == 8
    assert all(item["status"] == "not_started" for item in lessons)
    keys = {item["key"] for item in lessons}
    assert {"sqli", "missing-headers", "open-redirect"} <= keys

    detail = admin.get("/api/lessons/missing-headers").json()
    assert detail["has_probe"] is True
    assert detail["owasp_web"].startswith("A05")
    assert "concept" in detail and "fix" in detail

    assert admin.get("/api/lessons/does-not-exist").status_code == 404


def test_complete_persists_and_is_idempotent(clients):
    admin = clients()
    _login(admin)

    resp = admin.post("/api/lessons/sqli/complete")
    assert resp.status_code == 200 and resp.json()["status"] == "completed"

    lessons = admin.get("/api/lessons").json()
    assert next(item for item in lessons if item["key"] == "sqli")["status"] == "completed"

    # Marking again is a no-op success.
    assert admin.post("/api/lessons/sqli/complete").status_code == 200


def test_progress_is_per_user(clients):
    admin = clients()
    _login(admin)
    other = clients()
    _login(other, email="other@lab.local", role="analyst")

    admin.post("/api/lessons/xss/complete")

    lessons = other.get("/api/lessons").json()
    assert next(item for item in lessons if item["key"] == "xss")["status"] == "not_started"


def test_lessons_require_permission(clients):
    admin = clients()
    _login(admin)
    # A role with no permissions at all.
    admin.post("/api/admin/roles", json={"key": "noperm", "name": "No permissions"})

    user = clients()
    _login(user, email="restricted@lab.local", role="viewer")
    users = admin.get("/api/admin/users").json()
    uid = next(u["id"] for u in users if u["email"] == "restricted@lab.local")
    admin.post(f"/api/admin/users/{uid}/roles", json={"roles": ["noperm"]})

    assert user.get("/api/lessons").status_code == 403
    assert admin.get("/api/lessons").status_code == 200


def test_unauthenticated_lessons_is_401(client):
    assert client.get("/api/lessons").status_code == 401


def test_try_concept_only_lesson(clients):
    admin = clients()
    _login(admin)
    resp = admin.post("/api/lessons/sqli/try")  # sqli has no live probe
    assert resp.status_code == 200
    assert resp.json()["kind"] == "none"


def test_try_probe_lesson_returns_contrast(clients, monkeypatch):
    async def fake_run_probe(vuln_url, secure_url, probe):
        return {
            "kind": probe.kind,
            "explain": probe.explain,
            "vulnerable": {"reachable": True, "security_headers_present": 0, "max": 9},
            "hardened": {"reachable": True, "security_headers_present": 9, "max": 9},
        }

    monkeypatch.setattr(lessons_mod, "run_probe", fake_run_probe)

    admin = clients()
    _login(admin)
    body = admin.post("/api/lessons/missing-headers/try").json()
    assert body["kind"] == "headers"
    assert body["vulnerable"]["security_headers_present"] == 0
    assert body["hardened"]["security_headers_present"] == 9
