"""Stub/dev login.

Upserts a seeded dev user so CI and offline development can authenticate without
real OAuth providers. Only reachable when ``AUTH_STUB=1``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User

STUB_EMAIL = "dev@lab.local"


async def get_or_create_stub_user(session: AsyncSession) -> User:
    row = (
        await session.execute(select(User).where(User.email == STUB_EMAIL))
    ).scalar_one_or_none()
    if row is None:
        row = User(
            email=STUB_EMAIL,
            provider="stub",
            provider_sub="",
            name="Dev User",
            avatar="",
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return row
