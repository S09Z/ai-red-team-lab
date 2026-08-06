"""Stub/dev login.

Upserts a seeded dev user so CI and offline development can authenticate without
real OAuth providers. Only reachable when ``AUTH_STUB=1``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User
from ..rbac import assign_role

STUB_EMAIL = "dev@lab.local"


async def get_or_create_stub_user(
    session: AsyncSession, *, email: str = STUB_EMAIL, role: str = "admin"
) -> User:
    """Upsert a stub user. The default dev user is an admin; a different
    email/role lets dev + tests act as other roles (viewer, analyst, ...)."""
    row = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if row is None:
        row = User(
            email=email,
            provider="stub",
            provider_sub="",
            name="Dev User" if email == STUB_EMAIL else email.split("@")[0],
            avatar="",
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        await assign_role(session, row.id, role)
    return row
