# Phase 10 — Backend HTTP API Security (Hardened Reference Deployment)

> Build plan for a defense-in-depth counterpart to the vulnerable target.
> Checkbox summary lives in [`todo.md`](todo.md); this file is the detail.

## Context / why

The lab ships only a **deliberately vulnerable** Flask target
(`targets/flask-app/`) plus read-only tools that *measure* posture
(`header_inspector` scores 9 headers, `config_reader` flags
secrets/debug/exposed-ports, cookie checks want Secure+HttpOnly+SameSite).
There is **no defensive counterpart** — no reverse proxy, no WSGI server, no
TLS, no security headers, no rate limiting, no CORS/CSRF; secrets are
hardcoded and the container runs as root.

Phase 10 adds the missing half of the teaching loop: a **hardened reference
deployment** fronted by nginx. Learners run the *same tools* against
vulnerable vs. hardened and see the difference (`run_headers` 0/9 → 9/9;
`run_config` HIGH secrets → 0 findings). Every control maps to an OWASP
category.

**OWASP naming:** there is no finalized "OWASP Top 10 2026." Anchor to the
real canonical lists — **OWASP Top 10:2025 (web)** and **OWASP API Security
Top 10:2023** — which map cleanly onto the target's 8 vuln classes.

**Delivery:** three stacked sub-phase PRs continuing the one-branch-per-phase
pattern: `phase-10a-secure-app` → `phase-10b-nginx-proxy` →
`phase-10c-owasp-docs-ci`. Base `phase-10a` on `phase-9-readme` (current tip
of the open #8–#11 stack), or on `main` if that stack is merged first.

Leave the vulnerable app **unchanged** — it is the "before" half of the
contrast. This is defensive engineering, consistent with the lab's
read-only-assessment ethos (CLAUDE.md): it builds defenses, it does not
exploit.

---

## Phase 10a — Hardened app (`targets/flask-app-secure/`)

Secure counterpart of the same blog app. Use an **app factory**
(`create_app()`) so tests can drive a Flask `test_client`.

**Files (mirror the vulnerable app's shape):**

| File | Purpose |
|---|---|
| `app.py` | Same 16 routes, hardened; factory pattern |
| `security.py` | `@app.after_request` header injector + CORS allowlist helper |
| `config.py` | env-var driven (`os.environ.get(...)` + safe non-secret defaults) |
| `database.py` | seed with **hashed** passwords (`werkzeug.security`) |
| `templates/` | same pages, `\| safe` removed (autoescape), CSRF token fields |
| `static/app.js` | client script |
| `requirements.txt` | flask, pyjwt, werkzeug, flask-limiter, flask-wtf, flask-cors, gunicorn |
| `Dockerfile` | non-root user, `gunicorn` CMD (not the dev server) |

**Controls → the 8 vuln classes + selected layers:**

| Control | Fix | Verified by |
|---|---|---|
| 9 security headers via `after_request` | emit exactly the names in `header_inspector.SECURITY_HEADERS`: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, COOP, CORP, `X-XSS-Protection: 0` | `run_headers` → 9/9 |
| Secure session cookies | `SESSION_COOKIE_SECURE/HTTPONLY=True`, `SAMESITE="Lax"` | `_inspect_cookies` → 0 issues |
| SQLi (login) | parameterized query | code review + test |
| IDOR (profile update, `/api/user`) | ownership check + auth required | test |
| Reflected/stored XSS | remove `\| safe`, Jinja autoescape, CSP | code review |
| Broken auth / weak JWT | secret from env, short expiry, **re-verify `is_admin` against DB** | test |
| Open redirect | relative/allowlist-only validation of `next` | test |
| Sensitive data exposure | hash passwords, drop `/debug`, minimize `/api/*` fields | test |
| Debug off | `DEBUG=False` | `run_config` |
| Secrets | from env vars, no literals in `config.py` | `run_config` → 0 HIGH |
| Rate limiting | `flask-limiter` on `/login`, `/api/token`, state-changing POSTs | test |
| CORS lockdown | explicit same-origin allowlist (not wildcard) | test |
| CSRF tokens | `flask-wtf` CSRFProtect on all state-changing forms | test |

> Note: `X-XSS-Protection: 0` is the modern best practice (the legacy filter
> is deprecated); the inspector only checks presence + non-empty, so `0`
> still scores. Worth a one-line comment in `security.py`.

**Reuse:** `header_inspector.SECURITY_HEADERS` is the authoritative list of the
9 header names to emit. `config_reader` flags env-var *references* as INFO
(not HIGH), so env-based config scores 0 HIGH automatically.

**Tests** (match `tests/` patterns — `-ra`, `pythonpath=["src"]`, fixtures
`mocked_responses` / `temp_config_file`):
- `tests/test_secure_app_headers.py` — drive `create_app().test_client()`, feed response headers into `header_inspector.inspect()`, assert 9/9 + 0 cookie issues.
- `tests/test_secure_app_authz.py` — SQLi login rejected, IDOR blocked, open-redirect rejected, `/api/users` has no password field, `/debug` → 404.
- `tests/test_secure_config.py` — `config_reader.read_config()` on secure config → 0 HIGH.
- Add the secure app dir to the test path (small `conftest.py` addition or in-test `sys.path` insert, same idea as the tool bootstrap).

**Verify 10a:** `docker build targets/flask-app-secure` → run →
`run_headers` 9/9 · `run_config targets/flask-app-secure/config.py` 0 HIGH ·
`pytest -q` green · `ruff check` clean.

---

## Phase 10b — nginx reverse proxy (`deploy/nginx/`, `docker-compose.secure.yml`)

Edge layer in front of the hardened app. The app runs on an **internal**
network only; nginx is the sole host-exposed service.

**Files:**
- `deploy/nginx/nginx.conf` — TLS termination (self-signed lab cert), `server_tokens off`, edge security headers (belt-and-suspenders), `limit_req_zone` on `/login`, `client_max_body_size`, `proxy_pass` → gunicorn.
- `deploy/nginx/Dockerfile` — nginx base + build-step `openssl` self-signed **lab** cert (do not commit keys).
- `docker-compose.secure.yml` — `secure-app` (gunicorn, no host port, internal net) + `nginx` (`8443:443`, `8080:80`), healthchecks on both, isolated network.

**TLS vs. tool-measurability (decide at build time):** the tools use
`requests` with default TLS verification, so they can't hit a self-signed
HTTPS endpoint directly.
- **Option A (recommended):** nginx also serves plain HTTP `:8080` with the
  *same* security headers (no forced HTTPS redirect), so
  `run_headers --url http://localhost:8080/` measures the edge with zero tool
  changes. `:8443` gives real TLS for `curl -k` / browser demo.
- **Option B (stretch):** add opt-in `--insecure` to `run_http.py` /
  `run_headers.py` and a `verify: bool` param to `http_requester.fetch()`
  (+1 test). Small and broadly useful, but touches the Phase 2/3 library.

**Verify 10b:** `docker compose -f docker-compose.secure.yml up -d` → both
healthy · `curl -k https://localhost:8443/` = 200 ·
`run_headers --url http://localhost:8080/` = 9/9 · confirm `secure-app` is
**not** reachable directly from the host.

---

## Phase 10c — OWASP mapping + CI

**Files:**
- `docs/hardening.md` — per vuln class: OWASP id (2025 web + 2023 API) → control applied (app and/or edge) → verifying tool/test. Representative mapping:

  | Vuln | OWASP | Fix |
  |---|---|---|
  | SQLi | A03:2025 Injection | parameterized query |
  | IDOR | API1:2023 BOLA / A01 | ownership + auth |
  | XSS | A03 Injection | autoescape + CSP |
  | Weak JWT | API2:2023 Broken Auth / A07 | env secret + expiry + DB re-check |
  | Open redirect | A01 | allowlist |
  | Data exposure | API3:2023 / A02 Crypto Failures | hashing, drop `/debug` |
  | Missing headers/debug/cookies | A05 Misconfig / API8:2023 | `after_request`, secure cookies, DEBUG off |
  | No rate limit | API4:2023 Unrestricted Consumption | flask-limiter + nginx `limit_req` |
  | No CSRF | A01 | CSRF tokens |

- `.github/workflows/ci.yml` — `ruff check .` + `pytest -ra` on push/PR (no CI exists today); optional `docker build` smoke step for both targets.
- Update root `README.md` — add the secure deployment + link `docs/hardening.md`.
- Update `todo.md` — check Phase 10 items as built.

**Verify 10c:** links resolve · CI green in Actions · mapping table matches
the controls actually implemented in 10a/10b.

---

## End-to-end verification (whole phase)

1. `docker compose up -d` (vulnerable) → `run_headers` 0/9, `run_config targets/flask-app/config.py` HIGH secrets.
2. `docker compose -f docker-compose.secure.yml up -d` (hardened) → `run_headers http://localhost:8080/` 9/9, `run_config targets/flask-app-secure/config.py` 0 HIGH.
3. `pytest -q` — 28 existing + new secure tests green.
4. `ruff check .` clean.
5. Manual: `curl -k https://localhost:8443/` = 200; direct hit to the app container port from host refused.
