"""Static lesson registry — one per vulnerability class.

Each lesson is *content* (concept + OWASP ids + the hardened fix), plus an
optional **safe, GET-only** probe descriptor. A probe never exploits: it makes
a non-destructive observation against the lab's own targets (header counts, a
``/debug`` fetch, an open-redirect Location) to contrast vulnerable vs.
hardened behaviour. Flaw classes that can't be shown by a safe observation
(SQLi, IDOR, XSS, weak JWT, misconfig) are concept-only — the portal does not
weaponise them.
"""

from __future__ import annotations

from dataclasses import dataclass

# Probe kinds:
#   "headers"  -> fetch path, evidence = count of the 9 security headers present
#   "status"   -> fetch path, evidence = status code + whether look_for is in body
#   "redirect" -> fetch path without following, evidence = status + Location header


@dataclass(frozen=True)
class Probe:
    kind: str
    path: str
    look_for: str = ""
    explain: str = ""


@dataclass(frozen=True)
class Lesson:
    key: str
    title: str
    vuln_class: str
    owasp_web: str
    owasp_api: str
    concept: str
    fix: str
    verified_by: str
    probe: Probe | None = None


LESSONS: tuple[Lesson, ...] = (
    Lesson(
        key="sqli",
        title="SQL Injection",
        vuln_class="SQL Injection",
        owasp_web="A03 Injection",
        owasp_api="",
        concept=(
            "The vulnerable login builds its SQL by string-concatenating the "
            "username, so input like `' OR '1'='1` changes the query's meaning "
            "and can bypass authentication."
        ),
        fix=(
            "The hardened app uses parameterized queries (`... WHERE username = ?`) "
            "so input is data, never code."
        ),
        verified_by="tests/test_secure_app_authz.py (SQLi login rejected)",
        probe=None,
    ),
    Lesson(
        key="idor",
        title="IDOR / Broken Object Level Authorization",
        vuln_class="IDOR",
        owasp_web="A01 Broken Access Control",
        owasp_api="API1:2023 BOLA",
        concept=(
            "The vulnerable profile-update trusts the object id in the URL without "
            "checking ownership, so one user can modify another's record."
        ),
        fix=(
            "The hardened app requires authentication and checks that the target id "
            "belongs to the caller (`user_id != current -> 403`)."
        ),
        verified_by="tests/test_secure_app_authz.py (IDOR blocked)",
        probe=None,
    ),
    Lesson(
        key="xss",
        title="Reflected / Stored XSS",
        vuln_class="Cross-Site Scripting",
        owasp_web="A03 Injection",
        owasp_api="",
        concept=(
            "The vulnerable app renders user input with `| safe`, disabling "
            "autoescaping, so markup in a search term or post is executed in the "
            "browser."
        ),
        fix=(
            "The hardened app relies on Jinja autoescaping (no `| safe`) and sets a "
            "restrictive Content-Security-Policy."
        ),
        verified_by="code review (no `| safe`) + run_headers (CSP present)",
        probe=None,
    ),
    Lesson(
        key="weak-jwt",
        title="Weak / Forgeable JWT",
        vuln_class="Broken Authentication",
        owasp_web="A07 Identification & Auth Failures",
        owasp_api="API2:2023 Broken Authentication",
        concept=(
            "The vulnerable token endpoint signs JWTs with a hardcoded secret and "
            "trusts an `is_admin` claim from the token itself."
        ),
        fix=(
            "The hardened app loads the secret from the environment, uses a short "
            "expiry, and re-checks admin status against the database."
        ),
        verified_by="tests/test_secure_app_authz.py + code review",
        probe=None,
    ),
    Lesson(
        key="open-redirect",
        title="Open Redirect",
        vuln_class="Open Redirect",
        owasp_web="A01 Broken Access Control",
        owasp_api="",
        concept=(
            "The vulnerable `/redirect` sends the browser to any `next` value, so "
            "an attacker can craft a link to your site that bounces to theirs."
        ),
        fix=(
            "The hardened app allows only same-site relative paths and rejects "
            "absolute or protocol-relative targets."
        ),
        verified_by="tests/test_secure_app_authz.py (open-redirect rejected)",
        probe=Probe(
            kind="redirect",
            path="/redirect?next=https://example.com/",
            explain=(
                "The vulnerable target returns a 302 to example.com; the hardened "
                "target refuses and keeps you on the lab host."
            ),
        ),
    ),
    Lesson(
        key="data-exposure",
        title="Sensitive Data Exposure",
        vuln_class="Sensitive Data Exposure",
        owasp_web="A02 Cryptographic Failures",
        owasp_api="API3:2023 Excessive Data Exposure",
        concept=(
            "The vulnerable app exposes a `/debug` endpoint that dumps configuration "
            "(including secrets) and stores passwords in plaintext."
        ),
        fix=(
            "The hardened app removes `/debug` (404), hashes passwords, and "
            "minimizes API payloads."
        ),
        verified_by="tests/test_secure_app_authz.py (/debug -> 404)",
        probe=Probe(
            kind="status",
            path="/debug",
            look_for="SECRET",
            explain=(
                "The vulnerable target returns 200 with config/secrets in the body; "
                "the hardened target returns 404."
            ),
        ),
    ),
    Lesson(
        key="security-misconfig",
        title="Security Misconfiguration",
        vuln_class="Security Misconfiguration",
        owasp_web="A05 Security Misconfiguration",
        owasp_api="API8:2023 Security Misconfiguration",
        concept=(
            "The vulnerable app runs with debug mode on and verbose errors, leaking "
            "stack traces and internals."
        ),
        fix=(
            "The hardened app disables debug, sets secure cookies, and runs behind "
            "an nginx edge with `server_tokens off`."
        ),
        verified_by="run_config (DEBUG off, 0 HIGH) + run_headers",
        probe=None,
    ),
    Lesson(
        key="missing-headers",
        title="Missing Security Headers",
        vuln_class="Security Misconfiguration",
        owasp_web="A05 Security Misconfiguration",
        owasp_api="API8:2023 Security Misconfiguration",
        concept=(
            "The vulnerable app sets none of the standard security response headers, "
            "leaving clients without HSTS, CSP, framing, or MIME protections."
        ),
        fix=(
            "The hardened app emits all nine headers via an after_request hook, "
            "re-asserted at the nginx edge."
        ),
        verified_by="run_headers (0/9 -> 9/9)",
        probe=Probe(
            kind="headers",
            path="/",
            explain=(
                "The vulnerable target scores 0/9 security headers; the hardened "
                "target scores 9/9."
            ),
        ),
    ),
)

_BY_KEY = {lesson.key: lesson for lesson in LESSONS}


def get_lesson(key: str) -> Lesson | None:
    return _BY_KEY.get(key)


def _base_dict(lesson: Lesson) -> dict:
    return {
        "key": lesson.key,
        "title": lesson.title,
        "vuln_class": lesson.vuln_class,
        "owasp_web": lesson.owasp_web,
        "owasp_api": lesson.owasp_api,
        "has_probe": lesson.probe is not None,
    }


def lesson_summaries() -> list[dict]:
    return [_base_dict(lesson) for lesson in LESSONS]


def lesson_detail(lesson: Lesson) -> dict:
    data = _base_dict(lesson)
    data.update(
        concept=lesson.concept,
        fix=lesson.fix,
        verified_by=lesson.verified_by,
        probe_explain=lesson.probe.explain if lesson.probe else "",
    )
    return data
