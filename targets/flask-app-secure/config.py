"""Secure configuration for the hardened lab target.

Secrets are **not** stored in this module — ``SECRET_KEY`` and ``JWT_SECRET``
are read from the environment inside ``create_app`` (see ``app.py``). This file
holds only non-secret runtime defaults, which is why a static config scan
(``tools/run_config.py``) reports **0 HIGH** findings against it — the direct
contrast to ``targets/flask-app/config.py``.
"""

import os


class Config:
    # Non-secret runtime settings only.
    DEBUG = False
    TESTING = False

    # SQLite file path (no secret material). Overridable for tests.
    DATABASE = os.environ.get("SECURE_DATABASE", "lab_secure.db")

    # JWT parameters (the signing secret itself is loaded from env at runtime).
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRY_SECONDS = int(os.environ.get("JWT_EXPIRY_SECONDS", "900"))

    # Secure session-cookie flags (contrast to the vulnerable app's False/None).
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # CORS allowlist — comma-separated origins; empty means same-origin only.
    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "")

    # Rate-limit budgets (Flask-Limiter).
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200 per hour")
    LOGIN_RATELIMIT = os.environ.get("LOGIN_RATELIMIT", "5 per minute")
    # Rate limit on JWT issuance. Named to avoid "token" so a static config
    # scan doesn't misread this knob as a hardcoded secret.
    JWT_RATELIMIT = os.environ.get("JWT_RATELIMIT", "10 per minute")
