"""Environment-driven settings for the portal API.

Mirrors the hardened Flask target's posture: no secret literals in code, all
config from the environment. Field names map to upper-case env vars, e.g.
``portal_secret_key`` <- ``PORTAL_SECRET_KEY``.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Session signing secret. Empty -> an ephemeral random value is generated
    # at app startup (fine for dev/CI; set a stable value in real deployments).
    portal_secret_key: str = ""

    # Stub/dev login. When true, POST /auth/stub issues a session for a seeded
    # dev user so CI and offline development work without real OAuth providers.
    auth_stub: bool = False

    database_url: str = "sqlite+aiosqlite:///./portal.db"

    # The SPA origin; CORS is locked to exactly this.
    frontend_origin: str = "http://localhost:5173"

    # Base URL the OAuth providers redirect back to (this API).
    oauth_redirect_base: str = "http://localhost:8000"

    github_client_id: str = ""
    github_client_secret: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""

    # Session cookie flags. Secure defaults to True (production posture); set
    # False for plain-HTTP local/CI so the test client round-trips the cookie.
    cookie_secure: bool = True

    # Fixed lab target URLs for the lessons' safe "try it" observations. These
    # are the ONLY hosts a probe may contact (no user-supplied URLs), so there
    # is no SSRF surface. Point them at the running lab targets.
    vuln_target_url: str = "http://localhost:5000"
    secure_target_url: str = "http://localhost:8080"

    @property
    def github_configured(self) -> bool:
        return bool(self.github_client_id and self.github_client_secret)

    @property
    def google_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)
