"""Portal API application factory.

Builds a secure-by-default FastAPI app: 9 security headers, CORS locked to the
SPA origin, a signed HttpOnly+Secure+SameSite session cookie, and stub/OAuth
auth. Mirrors the hardened Flask target's ``create_app()`` posture.
"""

from __future__ import annotations

import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .admin import router as admin_router
from .auth.oauth import build_oauth
from .auth.router import router as auth_router
from .db import Base, make_engine, make_sessionmaker
from .lessons import router as lessons_router
from .rbac import seed_rbac
from .security import SecurityHeadersMiddleware, make_serializer
from .settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    secret_key = settings.portal_secret_key or secrets.token_hex(32)

    engine = make_engine(settings.database_url)
    sessionmaker = make_sessionmaker(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with sessionmaker() as session:
            await seed_rbac(session)
        yield
        await engine.dispose()

    app = FastAPI(title="AI Red Team Lab — Portal API", lifespan=lifespan)

    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = sessionmaker
    app.state.serializer = make_serializer(secret_key)
    app.state.oauth = build_oauth(settings)

    # OAuth state storage for Authlib (only exercised when a provider is set up).
    app.add_middleware(SessionMiddleware, secret_key=secret_key, same_site="lax",
                       https_only=settings.cookie_secure)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(lessons_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


# Uvicorn entrypoint: `uvicorn app.main:app`.
app = create_app()
