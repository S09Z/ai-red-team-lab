"""Security headers middleware and signed session-cookie helpers.

The header names match ``ai_red_team_lab.header_inspector.SECURITY_HEADERS`` and
the values mirror the hardened Flask target's ``security.py`` so the portal
scores 9/9 when dogfooded with ``tools/run_headers.py``. The session cookie is
HttpOnly + Secure + SameSite=Lax — the deliberate "done right" contrast to the
vulnerable app's localStorage token handling.
"""

from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

SESSION_COOKIE = "portal_session"
# 12 hours, in seconds.
SESSION_MAX_AGE = 12 * 60 * 60
_SESSION_SALT = "portal-session"

# A JSON API serves no HTML, so the CSP can be maximally restrictive while still
# being a non-empty, present header (which is what the inspector scores).
_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"

SECURITY_HEADERS: dict[str, str] = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": _CSP,
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    # Modern best practice: disable the deprecated legacy XSS auditor.
    "X-XSS-Protection": "0",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        return response


def make_serializer(secret_key: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key, salt=_SESSION_SALT)


def issue_session(response: Response, serializer: URLSafeTimedSerializer,
                  user_id: int, *, secure: bool) -> None:
    token = serializer.dumps({"user_id": user_id})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


def read_session_user_id(serializer: URLSafeTimedSerializer,
                         token: str | None) -> int | None:
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    user_id = data.get("user_id")
    return user_id if isinstance(user_id, int) else None
