"""Admin CRUD: users, roles, features, and the permission matrix.

Every endpoint is gated on the ``users`` feature — read to view, create to add a
role, update to change the permission matrix or a user's role assignment. A
viewer (no ``users`` grants) gets 403; granting the role ``users`` permissions
immediately unlocks these endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session
from .models import Feature, Permission, Role, User, user_roles
from .rbac import require, role_keys_for_user

# Under /api so the prefix can't collide with the SPA's own /admin client route.
router = APIRouter(prefix="/api/admin")


class RoleCreate(BaseModel):
    key: str
    name: str = ""
    description: str = ""


class PermissionMatrix(BaseModel):
    # feature key -> granted actions, e.g. {"lessons": ["read", "update"]}
    permissions: dict[str, list[str]]


class RoleAssignment(BaseModel):
    roles: list[str]


async def _feature_key_map(session: AsyncSession) -> dict[int, str]:
    rows = (await session.execute(select(Feature))).scalars().all()
    return {f.id: f.key for f in rows}


async def _role_matrix(session: AsyncSession, role_id: int) -> dict[str, list[str]]:
    keys = await _feature_key_map(session)
    perms = (
        await session.execute(select(Permission).where(Permission.role_id == role_id))
    ).scalars().all()
    return {keys[p.feature_id]: p.granted_actions() for p in perms if p.granted_actions()}


def _role_dict(role: Role, matrix: dict[str, list[str]]) -> dict:
    return {
        "id": role.id,
        "key": role.key,
        "name": role.name,
        "description": role.description,
        "permissions": matrix,
    }


@router.get("/features")
async def list_features(
    _: User = Depends(require("users", "read")),
    session: AsyncSession = Depends(get_session),
):
    rows = (await session.execute(select(Feature).order_by(Feature.key))).scalars().all()
    return [{"id": f.id, "key": f.key, "name": f.name} for f in rows]


@router.get("/users")
async def list_users(
    _: User = Depends(require("users", "read")),
    session: AsyncSession = Depends(get_session),
):
    users = (await session.execute(select(User).order_by(User.id))).scalars().all()
    return [
        {**u.public_dict(), "roles": await role_keys_for_user(session, u.id)} for u in users
    ]


@router.get("/roles")
async def list_roles(
    _: User = Depends(require("users", "read")),
    session: AsyncSession = Depends(get_session),
):
    roles = (await session.execute(select(Role).order_by(Role.key))).scalars().all()
    return [_role_dict(r, await _role_matrix(session, r.id)) for r in roles]


@router.post("/roles", status_code=201)
async def create_role(
    body: RoleCreate,
    _: User = Depends(require("users", "create")),
    session: AsyncSession = Depends(get_session),
):
    exists = (
        await session.execute(select(Role).where(Role.key == body.key))
    ).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=409, detail="role already exists")
    role = Role(key=body.key, name=body.name, description=body.description)
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return _role_dict(role, {})


@router.put("/roles/{role_id}/permissions")
async def set_role_permissions(
    role_id: int,
    body: PermissionMatrix,
    _: User = Depends(require("users", "update")),
    session: AsyncSession = Depends(get_session),
):
    role = await session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="role not found")
    features = {f.key: f for f in (await session.execute(select(Feature))).scalars().all()}
    for feature_key, actions in body.permissions.items():
        feature = features.get(feature_key)
        if feature is None:
            raise HTTPException(status_code=422, detail=f"unknown feature: {feature_key}")
        row = (
            await session.execute(
                select(Permission).where(
                    Permission.role_id == role_id, Permission.feature_id == feature.id
                )
            )
        ).scalar_one_or_none()
        if row is None:
            row = Permission(role_id=role_id, feature_id=feature.id)
            session.add(row)
        row.apply_actions(set(actions))
    await session.commit()
    return _role_dict(role, await _role_matrix(session, role_id))


@router.post("/users/{user_id}/roles")
async def set_user_roles(
    user_id: int,
    body: RoleAssignment,
    _: User = Depends(require("users", "update")),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    roles = (
        await session.execute(select(Role).where(Role.key.in_(body.roles)))
    ).scalars().all()
    found = {r.key for r in roles}
    missing = set(body.roles) - found
    if missing:
        raise HTTPException(status_code=422, detail=f"unknown roles: {sorted(missing)}")
    await session.execute(user_roles.delete().where(user_roles.c.user_id == user_id))
    for role in roles:
        await session.execute(
            user_roles.insert().values(user_id=user_id, role_id=role.id)
        )
    await session.commit()
    return {**user.public_dict(), "roles": sorted(found)}
