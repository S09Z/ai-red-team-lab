"""Modular RBAC: /me permissions, enforcement, grant-unlocks, matrix round-trip."""

from __future__ import annotations


def _login(c, *, email=None, role=None):
    body = {}
    if email:
        body["email"] = email
    if role:
        body["role"] = role
    return c.post("/auth/stub", json=body or None)


def _role(admin, key):
    roles = admin.get("/api/admin/roles").json()
    return next(r for r in roles if r["key"] == key)


def test_me_includes_roles_and_permissions(clients):
    admin = clients()
    _login(admin)
    me = admin.get("/me").json()
    assert me["roles"] == ["admin"]
    assert set(me["permissions"]["users"]) == {"create", "read", "update", "delete"}


def test_viewer_forbidden_admin_allowed(clients):
    admin = clients()
    _login(admin)
    viewer = clients()
    _login(viewer, email="viewer@lab.local", role="viewer")

    assert viewer.get("/api/admin/users").status_code == 403
    assert admin.get("/api/admin/users").status_code == 200


def test_granting_permission_unlocks_endpoint(clients):
    admin = clients()
    _login(admin)
    viewer = clients()
    _login(viewer, email="viewer@lab.local", role="viewer")

    assert viewer.get("/api/admin/users").status_code == 403

    viewer_role = _role(admin, "viewer")
    resp = admin.put(
        f"/api/admin/roles/{viewer_role['id']}/permissions",
        json={"permissions": {"users": ["read"]}},
    )
    assert resp.status_code == 200

    # Effective permissions are recomputed per request -> now unlocked.
    assert viewer.get("/api/admin/users").status_code == 200


def test_permission_matrix_round_trips(clients):
    admin = clients()
    _login(admin)
    analyst = _role(admin, "analyst")

    admin.put(
        f"/api/admin/roles/{analyst['id']}/permissions",
        json={"permissions": {"reports": ["create", "read", "update"]}},
    )
    updated = _role(admin, "analyst")
    assert set(updated["permissions"]["reports"]) == {"create", "read", "update"}


def test_assign_roles_to_user(clients):
    admin = clients()
    _login(admin)
    viewer = clients()
    _login(viewer, email="viewer@lab.local", role="viewer")

    users = admin.get("/api/admin/users").json()
    target = next(u for u in users if u["email"] == "viewer@lab.local")

    resp = admin.post(f"/api/admin/users/{target['id']}/roles", json={"roles": ["analyst"]})
    assert resp.status_code == 200
    assert resp.json()["roles"] == ["analyst"]


def test_unauthenticated_admin_is_401(client):
    assert client.get("/api/admin/users").status_code == 401
