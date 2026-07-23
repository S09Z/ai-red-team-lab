"""Read-only security-header audit.

Scores an HTTP response's security headers (0–9) and flags insecure cookie
attributes. This is pure analysis of already-observed headers — it makes no
network requests itself, so compose it with ``http_requester.fetch``
(CLAUDE.md §2 — read-only; Application Mapper / Secure Code Reviewer).
"""

from __future__ import annotations

from typing import Any

# The nine security headers scored, each with a one-line rationale.
SECURITY_HEADERS: dict[str, str] = {
    "strict-transport-security": "Enforce HTTPS (HSTS)",
    "content-security-policy": "Restrict resource origins (CSP)",
    "x-frame-options": "Prevent clickjacking",
    "x-content-type-options": "Block MIME sniffing",
    "referrer-policy": "Limit referrer leakage",
    "permissions-policy": "Restrict powerful browser features",
    "cross-origin-opener-policy": "Isolate browsing context (COOP)",
    "cross-origin-resource-policy": "Restrict cross-origin embedding (CORP)",
    "x-xss-protection": "Legacy reflected-XSS filter",
}


def inspect(headers: dict) -> dict[str, Any]:
    """Audit security headers in a response header mapping.

    Header lookups are case-insensitive. Returns a dict with:
      - ``score`` / ``max_score``  count present out of 9
      - ``present``   list of {header, value}
      - ``missing``   list of {header, rationale}
      - ``cookie_issues``  list of Set-Cookie attribute warnings
    """
    normalized = {str(k).lower(): v for k, v in dict(headers).items()}

    present: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for name, rationale in SECURITY_HEADERS.items():
        value = normalized.get(name)
        if value is not None and str(value).strip():
            present.append({"header": name, "value": value})
        else:
            missing.append({"header": name, "rationale": rationale})

    return {
        "score": len(present),
        "max_score": len(SECURITY_HEADERS),
        "present": present,
        "missing": missing,
        "cookie_issues": _inspect_cookies(normalized.get("set-cookie")),
    }


def _inspect_cookies(set_cookie: Any) -> list[str]:
    """Flag missing Secure / HttpOnly / SameSite attributes on Set-Cookie."""
    if not set_cookie:
        return []
    lowered = str(set_cookie).lower()
    issues = []
    if "secure" not in lowered:
        issues.append("Set-Cookie missing Secure attribute")
    if "httponly" not in lowered:
        issues.append("Set-Cookie missing HttpOnly attribute")
    if "samesite" not in lowered:
        issues.append("Set-Cookie missing SameSite attribute")
    return issues
