"""Authlib OAuth registration, gated on configured provider secrets.

Only providers whose client id/secret are present in the environment are
registered. Unconfigured providers simply aren't in the registry, and their
routes return 503 (see ``router``). Real providers require internet + registered
OAuth apps; the stub login (``AUTH_STUB=1``) covers CI/offline dev.
"""

from __future__ import annotations

from authlib.integrations.starlette_client import OAuth

from ..settings import Settings


def build_oauth(settings: Settings) -> OAuth:
    oauth = OAuth()
    if settings.github_configured:
        oauth.register(
            name="github",
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "read:user user:email"},
        )
    if settings.google_configured:
        oauth.register(
            name="google",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            server_metadata_url=(
                "https://accounts.google.com/.well-known/openid-configuration"
            ),
            client_kwargs={"scope": "openid email profile"},
        )
    return oauth
