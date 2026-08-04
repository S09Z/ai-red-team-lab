# Hardening reference — vulnerable vs. hardened, mapped to OWASP

This lab ships two copies of the same blog app:

- `targets/flask-app/` — the **deliberately vulnerable** target (the "before").
- `targets/flask-app-secure/` — the **hardened reference** (the "after"),
  fronted at the edge by nginx (`deploy/nginx/`, `docker-compose.secure.yml`).

Run the *same* read-only tools against each and the difference is measurable:
`run_headers` 0/9 → **9/9**, `run_config` HIGH secrets → **0 HIGH**. Every
control below traces to a specific line in the hardened codebase and to the
tool or test that verifies it.

> **A note on OWASP versioning.** There is no finalized "OWASP Top 10 2026."
> This mapping anchors to the canonical lists — the **OWASP Top 10** web
> categories (A0x) and the **OWASP API Security Top 10:2023** (APIx:2023).
> Category numbers used here are the stable ones for these flaw classes; treat
> the ids as the framework anchor, not as a version claim.

## Measurement summary

| Signal | Vulnerable | Hardened | Measured by |
|---|---|---|---|
| Security headers | 0/9 | **9/9** | `run_headers` |
| Config HIGH findings (secrets/debug) | HIGH secrets, `DEBUG=True` | **0 HIGH** | `run_config` |
| Session-cookie flags | missing | Secure + HttpOnly + SameSite=Lax | `run_headers` (cookie check) |
| `/debug` config dump | 200 | **404** (route removed) | manual / test |

## Control mapping

Legend for "Layer": **app** = Flask code in `targets/flask-app-secure/`,
**edge** = nginx in `deploy/nginx/`.

| # | Vuln class | OWASP (web) | OWASP (API) | Control applied | Layer | Verified by |
|---|---|---|---|---|---|---|
| 1 | SQL injection | A03 Injection | — | Parameterized queries (`?` placeholders) on every DB call, incl. login `SELECT ... WHERE username = ?` | app | `tests/test_secure_app_authz.py` (SQLi login rejected) + code review |
| 2 | IDOR / broken object access | A01 Broken Access Control | API1:2023 BOLA | Auth required + ownership check (`user_id != _uid() → 403`) on profile update and `/api/user*` | app | `tests/test_secure_app_authz.py` (IDOR blocked) |
| 3 | Reflected / stored XSS | A03 Injection | — | Jinja autoescape (no `\| safe`) + restrictive CSP (`default-src 'self'`, no inline script) | app + edge | code review (no `\| safe`) + `run_headers` (CSP present) |
| 4 | Weak / forgeable JWT | A07 Identification & Auth Failures | API2:2023 Broken Auth | Signing secret from env (never a literal), short expiry (`JWT_EXPIRY_SECONDS=900`), `sub`-only claim, admin re-checked from DB (`_current_user_is_admin`) | app | `tests/test_secure_app_authz.py` + code review |
| 5 | Open redirect | A01 Broken Access Control | — | `_is_safe_next` allows only same-site relative paths; rejects scheme, host, and protocol-relative `//` | app | `tests/test_secure_app_authz.py` (open-redirect rejected) |
| 6 | Sensitive data exposure | A02 Cryptographic Failures | API3:2023 Excessive Data Exposure | Passwords hashed (`werkzeug.security`), API payloads minimized (`/api/users` → id+username only), `/debug` route removed | app | `tests/test_secure_app_authz.py` (no password field; `/debug` → 404) |
| 7 | Security misconfiguration | A05 Security Misconfiguration | API8:2023 Security Misconfiguration | 9 security headers via `after_request`; `DEBUG=False`; secure session cookies; `server_tokens off` at the edge | app + edge | `run_headers` 9/9 · `run_config` 0 HIGH · cookie check 0 issues |
| 8 | Hardcoded secrets | A05 Security Misconfiguration | — | `SECRET_KEY` / `JWT_SECRET` read from env with an ephemeral random fallback; no literals in `config.py` | app | `run_config` → 0 HIGH |
| 9 | Missing rate limiting | — | API4:2023 Unrestricted Resource Consumption | Flask-Limiter on `/login` (5/min) and `/api/token` (10/min) **plus** nginx `limit_req` (10 r/m) on `/login` | app + edge | code review (`app.py`, `nginx.conf`) |
| 10 | Permissive CORS | A05 Security Misconfiguration | API8:2023 Security Misconfiguration | Explicit origin allowlist only (never a wildcard); empty list = no cross-origin | app | code review (`_configure_cors`) |
| 11 | Missing CSRF protection | A01 Broken Access Control | — | Flask-WTF `CSRFProtect` on state-changing forms (`/api/token` is `@csrf.exempt` as a credential endpoint) | app | code review (`csrf.init_app`) |
| 12 | No transport encryption | A02 Cryptographic Failures | — | nginx TLS termination on `:443` (self-signed lab cert) + HSTS header | edge | `curl -k https://localhost:8443/` = 200 · `run_headers` (HSTS present) |
| 13 | Direct exposure of app server | A05 Security Misconfiguration | API8:2023 Security Misconfiguration | App on an internal-only network (gunicorn, no host port); nginx is the sole host-exposed service | edge | `docker ps` (app shows `5000/tcp`, no host binding) |

## Source-of-truth references

| Control area | File |
|---|---|
| Security headers + CSP | `targets/flask-app-secure/security.py` |
| Routes / authz / JWT / redirect / CSRF / CORS | `targets/flask-app-secure/app.py` |
| Non-secret config, cookie flags, rate-limit budgets | `targets/flask-app-secure/config.py` |
| Hashed-password seed | `targets/flask-app-secure/database.py` |
| Edge headers, TLS, `limit_req`, `server_tokens off` | `deploy/nginx/nginx.conf`, `deploy/nginx/app_proxy.conf` |
| Internal network / port isolation | `docker-compose.secure.yml` |
| Authoritative header list (9 names) | `src/ai_red_team_lab/header_inspector.py` |

## Reproduce the contrast

```bash
# Vulnerable "before"
docker compose up -d
python tools/run_headers.py --url http://localhost:5000/          # 0/9
python tools/run_config.py  --file targets/flask-app/config.py    # HIGH secrets
docker compose down

# Hardened "after" (app internal-only, nginx at the edge)
docker compose -f docker-compose.secure.yml up -d --build
python tools/run_headers.py --url http://localhost:8080/          # 9/9
python tools/run_config.py  --file targets/flask-app-secure/config.py  # 0 HIGH
curl -k https://localhost:8443/                                    # 200 (TLS)
docker compose -f docker-compose.secure.yml down
```
