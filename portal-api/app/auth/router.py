"""Auth + identity routes.

Endpoints:
  POST /auth/stub                 stub/dev login (AUTH_STUB=1 only)
  GET  /auth/{provider}/login     start OAuth (github|google), 503 if unconfigured
  GET  /auth/{provider}/callback  finish OAuth, issue session, redirect to SPA
  POST /auth/logout               clear session
  GET  /me                        current user or 401
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import get_current_user
from ..models import User
from ..rbac import effective_permissions, permissions_payload, role_keys_for_user
from ..security import clear_session, issue_session
from .stub import STUB_EMAIL, get_or_create_stub_user

router = APIRouter()

_PROVIDERS = {"github", "google"}


class StubLogin(BaseModel):
    email: str | None = None
    role: str | None = None


def _issue(request: Request, response, user_id: int) -> None:
    issue_session(
        response,
        request.app.state.serializer,
        user_id,
        secure=request.app.state.settings.cookie_secure,
    )


@router.post("/auth/stub")
async def auth_stub(
    request: Request,
    body: StubLogin | None = None,
    session: AsyncSession = Depends(get_session),
):
    if not request.app.state.settings.auth_stub:
        raise HTTPException(status_code=404, detail="stub login disabled")
    email = body.email if body and body.email else STUB_EMAIL
    role = body.role if body and body.role else "admin"
    user = await get_or_create_stub_user(session, email=email, role=role)
    response = JSONResponse(user.public_dict())
    _issue(request, response, user.id)
    return response


@router.get("/auth/{provider}/login")
async def oauth_login(provider: str, request: Request):
    if provider not in _PROVIDERS:
        raise HTTPException(status_code=404, detail="unknown provider")
    oauth = request.app.state.oauth
    client = oauth.create_client(provider)
    if client is None:
        raise HTTPException(status_code=503, detail=f"{provider} OAuth not configured")
    base = request.app.state.settings.oauth_redirect_base.rstrip("/")
    redirect_uri = f"{base}/auth/{provider}/callback"
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/auth/{provider}/callback")
async def oauth_callback(
    provider: str, request: Request, session: AsyncSession = Depends(get_session)
):
    if provider not in _PROVIDERS:
        raise HTTPException(status_code=404, detail="unknown provider")
    oauth = request.app.state.oauth
    client = oauth.create_client(provider)
    if client is None:
        raise HTTPException(status_code=503, detail=f"{provider} OAuth not configured")

    token = await client.authorize_access_token(request)
    profile = await _fetch_profile(provider, client, token)
    user = await _resolve_user(session, provider=provider, profile=profile)

    frontend = request.app.state.settings.frontend_origin
    response = RedirectResponse(url=frontend, status_code=302)
    _issue(request, response, user.id)
    return response


@router.post("/auth/logout")
async def logout():
    response = JSONResponse({"status": "logged_out"})
    clear_session(response)
    return response


@router.get("/me")
async def me(
    user: User | None = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if user is None:
        raise HTTPException(status_code=401, detail="not authenticated")
    perms = await effective_permissions(session, user.id)
    roles = await role_keys_for_user(session, user.id)
    return {
        **user.public_dict(),
        "roles": roles,
        "permissions": permissions_payload(perms),
    }


async def _fetch_profile(provider: str, client, token: dict) -> dict:
    """Best-effort profile fetch (scaffold; exercised only with live providers)."""
    if provider == "google":
        info = token.get("userinfo") or {}
        return {
            "email": info.get("email", ""),
            "sub": str(info.get("sub", "")),
            "name": info.get("name", ""),
            "avatar": info.get("picture", ""),
        }
    # github
    resp = await client.get("user", token=token)
    data = resp.json()
    return {
        "email": data.get("email") or f"{data.get('login', 'user')}@users.github",
        "sub": str(data.get("id", "")),
        "name": data.get("name") or data.get("login", ""),
        "avatar": data.get("avatar_url", ""),
    }


async def _resolve_user(session: AsyncSession, *, provider: str, profile: dict) -> User:
    email = profile["email"]
    row = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if row is None:
        row = User(
            email=email,
            provider=provider,
            provider_sub=profile["sub"],
            name=profile["name"],
            avatar=profile["avatar"],
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return row
