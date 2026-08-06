"""Modular RBAC: seeding, effective-permission resolution, and enforcement.

Features are the portal modules; a role grants modular CRUD per feature; a user
holds roles. ``require(feature, action)`` is the FastAPI dependency that gates
endpoints (401 if anonymous, 403 if the action isn't granted).
"""

from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session
from .deps import get_current_user
from .models import Feature, Permission, Role, User, user_roles

ACTIONS = ("create", "read", "update", "delete")
FEATURES = ("lessons", "tools", "targets", "reports", "docs", "users")

_ACTION_COL = {
    "create": "can_create",
    "read": "can_read",
    "update": "can_update",
    "delete": "can_delete",
}

# Default roles seeded at startup. perms: feature -> granted action set.
_SEED_ROLES: dict[str, dict] = {
    "admin": {
        "name": "Administrator",
        "description": "Full access to every feature.",
        "perms": {f: set(ACTIONS) for f in FEATURES},
    },
    "analyst": {
        "name": "Analyst",
        "description": "Read/update lessons, tools, reports, docs.",
        "perms": {f: {"read", "update"} for f in ("lessons", "tools", "reports", "docs")},
    },
    "viewer": {
        "name": "Viewer",
        "description": "Read-only across the modules.",
        "perms": {f: {"read"} for f in ("lessons", "tools", "targets", "reports", "docs")},
    },
}


async def _get_or_create_feature(session: AsyncSession, key: str) -> Feature:
    row = (await session.execute(select(Feature).where(Feature.key == key))).scalar_one_or_none()
    if row is None:
        row = Feature(key=key, name=key.capitalize())
        session.add(row)
        await session.flush()
    return row


async def _get_or_create_role(session: AsyncSession, key: str, name: str, desc: str) -> Role:
    row = (await session.execute(select(Role).where(Role.key == key))).scalar_one_or_none()
    if row is None:
        row = Role(key=key, name=name, description=desc)
        session.add(row)
        await session.flush()
    return row


async def _set_permission(
    session: AsyncSession, role_id: int, feature_id: int, actions: set[str]
) -> None:
    row = (
        await session.execute(
            select(Permission).where(
                Permission.role_id == role_id, Permission.feature_id == feature_id
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = Permission(role_id=role_id, feature_id=feature_id)
        session.add(row)
    row.apply_actions(actions)


async def seed_rbac(session: AsyncSession) -> None:
    """Idempotently seed the feature rows and the default roles + permissions."""
    features = {key: await _get_or_create_feature(session, key) for key in FEATURES}
    for role_key, cfg in _SEED_ROLES.items():
        role = await _get_or_create_role(session, role_key, cfg["name"], cfg["description"])
        for feature_key, actions in cfg["perms"].items():
            await _set_permission(session, role.id, features[feature_key].id, actions)
    await session.commit()


async def role_keys_for_user(session: AsyncSession, user_id: int) -> list[str]:
    rows = await session.execute(
        select(Role.key).join(user_roles, user_roles.c.role_id == Role.id).where(
            user_roles.c.user_id == user_id
        )
    )
    return sorted(rows.scalars().all())


async def effective_permissions(session: AsyncSession, user_id: int) -> dict[str, set[str]]:
    """OR the granted actions across all of the user's roles, keyed by feature."""
    rows = await session.execute(
        select(Feature.key, Permission)
        .join(Feature, Permission.feature_id == Feature.id)
        .join(user_roles, user_roles.c.role_id == Permission.role_id)
        .where(user_roles.c.user_id == user_id)
    )
    result: dict[str, set[str]] = {}
    for feature_key, perm in rows.all():
        granted = result.setdefault(feature_key, set())
        for action, col in _ACTION_COL.items():
            if getattr(perm, col):
                granted.add(action)
    return result


def permissions_payload(perms: dict[str, set[str]]) -> dict[str, list[str]]:
    """Serialize effective permissions for /me: feature -> sorted action list."""
    return {feature: sorted(actions) for feature, actions in perms.items() if actions}


def require(feature: str, action: str):
    """Dependency factory: 401 if anonymous, 403 unless (feature, action) is granted."""

    async def _dep(
        user: User | None = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> User:
        if user is None:
            raise HTTPException(status_code=401, detail="not authenticated")
        perms = await effective_permissions(session, user.id)
        if action not in perms.get(feature, set()):
            raise HTTPException(status_code=403, detail=f"missing {feature}:{action}")
        return user

    return _dep


async def assign_role(session: AsyncSession, user_id: int, role_key: str) -> None:
    """Grant a role to a user by role key (idempotent)."""
    role = (await session.execute(select(Role).where(Role.key == role_key))).scalar_one_or_none()
    if role is None:
        return
    existing = await session.execute(
        select(user_roles).where(
            user_roles.c.user_id == user_id, user_roles.c.role_id == role.id
        )
    )
    if existing.first() is None:
        await session.execute(user_roles.insert().values(user_id=user_id, role_id=role.id))
        await session.commit()
