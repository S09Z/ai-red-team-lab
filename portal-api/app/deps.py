"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session
from .models import User
from .security import SESSION_COOKIE, read_session_user_id


async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User | None:
    """Resolve the logged-in user from the signed session cookie, or None."""
    serializer = request.app.state.serializer
    user_id = read_session_user_id(serializer, request.cookies.get(SESSION_COOKIE))
    if user_id is None:
        return None
    return await session.get(User, user_id)
