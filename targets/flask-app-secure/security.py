"""Response security headers for the hardened lab target.

``register_security(app)`` installs an ``after_request`` hook that emits every
header scored by ``ai_red_team_lab.header_inspector`` (9/9) plus a restrictive
Content-Security-Policy. It is the defensive counterpart to the vulnerable
app, which sets none of these.
"""

from __future__ import annotations

from flask import Flask

# A conservative, self-hosted CSP: no inline scripts, no third-party origins.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)

# Header name -> value. Names match ``header_inspector.SECURITY_HEADERS`` so a
# response carrying these scores 9/9.
SECURITY_HEADERS: dict[str, str] = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    # Modern best practice is to disable the legacy, deprecated XSS auditor.
    # The inspector only checks presence + non-empty value, so "0" still scores.
    "X-XSS-Protection": "0",
}


def register_security(app: Flask) -> None:
    """Attach the response-header hook to ``app``."""

    @app.after_request
    def _set_security_headers(response):
        for name, value in SECURITY_HEADERS.items():
            response.headers[name] = value
        return response
