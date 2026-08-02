# AI Red Team Lab — Build TODO

## Phase 1 · Foundation
- [x] `pyproject.toml` — add description, fix author, add deps (`requests`, `beautifulsoup4`, `rich`, `click`) and dev deps (`pytest`, `pytest-cov`, `responses`, `flask`)
- [x] `src/ai_red_team_lab/__init__.py`
- [x] `tests/__init__.py`
- [x] `tests/conftest.py` — mock HTTP server fixture + temp config file fixture

## Phase 2 · Observation Library
- [x] `src/ai_red_team_lab/http_requester.py` — `fetch()` → status, headers, body excerpt, redirect chain
- [x] `src/ai_red_team_lab/port_enumerator.py` — `scan()` → open/closed/filtered via stdlib `socket` only
- [x] `src/ai_red_team_lab/js_harvester.py` — `harvest()` → extract scripts, scan for secrets/endpoints/comments
- [x] `src/ai_red_team_lab/header_inspector.py` — `inspect()` → audit 9 security headers, return score 0–9
- [x] `src/ai_red_team_lab/config_reader.py` — `read_config()` → static scan of compose/.env/yaml for secrets/debug flags

## Phase 3 · Tests
- [x] `tests/test_http_requester.py`
- [x] `tests/test_port_enumerator.py`
- [x] `tests/test_js_harvester.py`
- [x] `tests/test_header_inspector.py`
- [x] `tests/test_config_reader.py`

## Phase 3b · Security Hardening (from /security-review findings)
- [x] `src/ai_red_team_lab/js_harvester.py` — block SSRF: reject script `src` URLs that resolve to loopback / link-local / RFC 1918 IP literals before fetching
- [x] `tests/test_js_harvester.py` — add tests: link-local (169.254.x.x) blocked, loopback (127.x.x.x) blocked, normal external host still allowed

## Phase 4 · Flask Target
- [x] `targets/flask-app/config.py` — hardcoded secrets, DEBUG=True, insecure cookie flags, CSRF disabled
- [x] `targets/flask-app/database.py` — SQLite seed: users (plaintext passwords), posts, secrets (fake API key)
- [x] `targets/flask-app/app.py` — 16 vulnerable routes (SQLi, IDOR, XSS, broken auth, open redirect, etc.)
- [x] `targets/flask-app/static/app.js` — hardcoded API_BASE, dev token comment, insecure localStorage
- [x] `targets/flask-app/templates/` — base, index, login, dashboard, profile, admin, post, search
- [x] `targets/flask-app/requirements.txt` — `flask`, `pyjwt`
- [x] `targets/flask-app/Dockerfile`

## Phase 5 · Docker Compose
- [x] `docker-compose.yml` — flask-app service, port 5000, isolated bridge network, healthcheck

## Phase 6 · Templates
- [x] `templates/finding-card.md` — 8-field evidence card (CLAUDE.md §6)
- [x] `templates/full-report.md` — 12-section report skeleton (CLAUDE.md §8)
- [x] `templates/role-checklist.md` — self-verification checklist (CLAUDE.md §10)

## Phase 7 · CLI Tools
- [x] `tools/README.md`
- [x] `tools/run_http.py`
- [x] `tools/run_ports.py`
- [x] `tools/run_js.py`
- [x] `tools/run_headers.py`
- [x] `tools/run_config.py`

## Phase 8 · Docs
- [x] `docs/setup.md` — prereqs, install, first run
- [x] `docs/workflow.md` — full assessment session walkthrough
- [x] `docs/roles.md` — role → trigger phrase → tools → output → restrictions
- [x] `docs/lab-scenario-01.md` — scope, role order, success criteria, spoiler-hidden findings

## Phase 9 · README
- [x] `README.md` — quick-start, what the lab is, links to docs

---

## Verification (run after all phases)
- [ ] `poetry install --with dev` — clean install
- [ ] `docker compose up -d` → `docker compose ps` shows healthy
- [ ] `python tools/run_http.py --url http://localhost:5000/` → 200
- [ ] `python tools/run_headers.py --url http://localhost:5000/` → score 0/9
- [ ] `python tools/run_js.py --url http://localhost:5000/` → ≥2 findings
- [ ] `python tools/run_config.py --file docker-compose.yml` → HIGH findings
- [ ] `python tools/run_ports.py --host localhost --ports 5000` → open
- [ ] `pytest tests/ -v` → all green

---

## Phase 10 · Backend HTTP API Security (Hardened Reference Deployment)
See `PHASE-10-PLAN.md` for full detail. Defense-in-depth counterpart to the
vulnerable target; anchored to OWASP Top 10:2025 (web) + API Security Top 10:2023.
Delivered as three stacked sub-phase PRs.

### Phase 10a · Hardened app (`targets/flask-app-secure/`) — DONE
- [x] `app.py` — `create_app()` factory, all 16 routes hardened
- [x] `security.py` — `@app.after_request` sets the 9 headers in `header_inspector.SECURITY_HEADERS`; CORS allowlist helper
- [x] `config.py` — env-var driven (no literal secrets → `run_config` 0 HIGH); `DEBUG=False`; secure session cookies
- [x] `database.py` — hashed passwords (`werkzeug.security`), no secrets-table exposure
- [x] `templates/` — `| safe` removed (autoescape), CSRF token fields
- [x] `requirements.txt` — flask, pyjwt, werkzeug, flask-limiter, flask-wtf, flask-cors, gunicorn
- [x] `Dockerfile` — non-root user, gunicorn CMD
- [x] Fixes: SQLi (parameterized), IDOR (ownership+auth), XSS (autoescape+CSP), weak JWT (env secret+expiry+DB re-check), open redirect (allowlist), data exposure (hash pw, drop `/debug`, minimize API fields)
- [x] Controls: rate limiting (flask-limiter), CORS lockdown, CSRF tokens
- [x] `tests/test_secure_app_headers.py` — `test_client` headers → `header_inspector` 9/9, 0 cookie issues
- [x] `tests/test_secure_app_authz.py` — SQLi/IDOR/open-redirect rejected, no pw in `/api/users`, `/debug` 404
- [x] `tests/test_secure_config.py` — `config_reader` → 0 HIGH (verified: 0 findings vs vulnerable 2 HIGH + 1 MEDIUM)

### Phase 10b · nginx reverse proxy (`deploy/nginx/`)
- [ ] `deploy/nginx/nginx.conf` — TLS (self-signed lab cert), `server_tokens off`, edge security headers, `limit_req_zone` on `/login`, `client_max_body_size`, `proxy_pass` → gunicorn
- [ ] `deploy/nginx/Dockerfile` — nginx base + build-time `openssl` self-signed cert (keys NOT committed)
- [ ] `docker-compose.secure.yml` — `secure-app` (gunicorn, internal net, no host port) + `nginx` (`8443:443`, `8080:80`), healthchecks
- [ ] Decision: **Option A** — nginx also serves plain HTTP `:8080` with same headers so tools measure with zero changes (`:8443` for TLS demo). Option B (stretch): add `--insecure`/`verify` to `run_http`/`run_headers`/`fetch()`

### Phase 10c · OWASP mapping + CI
- [ ] `docs/hardening.md` — per vuln: OWASP id (2025 web / 2023 API) → control → verifying tool/test
- [ ] `.github/workflows/ci.yml` — `ruff check .` + `pytest -ra` on push/PR (no CI exists today)
- [ ] Update `README.md` — link secure deployment + `docs/hardening.md`

### Phase 10 verification
- [ ] Vulnerable: `run_headers` 0/9, `run_config` HIGH — unchanged
- [ ] Hardened: `run_headers http://localhost:8080/` → 9/9, `run_config targets/flask-app-secure/config.py` → 0 HIGH
- [ ] `curl -k https://localhost:8443/` → 200; direct host hit to app container refused
- [ ] `pytest -q` (28 existing + new) green; `ruff check .` clean

---

## Phase 11 · Web Backoffice Portal (Control Plane)
See `PHASE-11-PLAN.md` for full detail. Secure FastAPI + React portal:
real GitHub/Google OAuth, modular RBAC (member/role/feature CRUD permissions),
Hacksplaining-style vuln lessons + tool launcher, docs viewer, target control,
report builder. Stacked sub-phase PRs 11a→11f. Portal is the SECURE control
plane (reuses Phase 10 hardening); lessons target the lab's OWN vuln app only.

### Phase 11a · Skeleton + OAuth
- [ ] `portal-api/` — FastAPI `create_app()`, env config, async SQLAlchemy, `/health`, non-root Dockerfile
- [ ] OAuth (Authlib): GitHub + Google auth-code flow; `/auth/{provider}/login|callback`, `/auth/logout`, `/me`; secrets via env (`.env.example`)
- [ ] Stub login (`AUTH_STUB=1`) for CI/offline
- [ ] Session as HttpOnly+Secure+SameSite=Lax cookie (NOT localStorage)
- [ ] `portal-web/` — Vite+React skeleton: login, auth context, protected routing, API client

### Phase 11b · Modular RBAC
- [ ] Models: users, roles, user_roles, features, permissions(role,feature,can_create/read/update/delete)
- [ ] Seed roles (admin/analyst/viewer) + feature rows (lessons/tools/targets/reports/docs/users)
- [ ] `require(feature, action)` FastAPI dependency → 403 on miss; `/me` returns effective permissions
- [ ] CRUD endpoints (users/roles/features/permissions; assign roles/permissions), RBAC-gated
- [ ] React admin UI: users table, role editor, permission matrix (features × CRUD); UI gated by permissions

### Phase 11c · Vuln lessons + progress
- [ ] Lesson schema per vuln class: concept + OWASP id → try-it (sandboxed, lab target only) → fix + verifying tool → complete
- [ ] `lessons` API + `lesson_progress` (per user)
- [ ] React lessons menu (cards + badges) + lesson runner (stepper)

### Phase 11d · Tool launcher + target control
- [ ] Launcher: `portal-api` imports `ai_red_team_lab` lib; RBAC-gated endpoints run tool vs target, return CLI-identical JSON
- [ ] React Tools tab: render results as evidence cards (0/9 vs 9/9, findings table)
- [ ] Target control (admin-only): start/stop/switch vuln vs hardened via docker compose — ALLOWLIST only (fixed files+actions, no user input), audited
- [ ] Gate target control behind `targets` update permission

### Phase 11e · Docs viewer + report builder
- [ ] Docs API serves `docs/*.md`; React markdown viewer + nav (gated by `docs`)
- [ ] Report builder: fill `templates/finding-card` + `full-report`; persist `report_drafts` per user; export markdown (gated by `reports`)

### Phase 11f · Hardening, deploy, CI
- [ ] Portal hardening: security headers, CORS→SPA origin, CSRF on cookie writes, rate-limit `/auth/*`, pydantic validation, no secrets in code
- [ ] `docker-compose.portal.yml` — portal-api + portal-web + db (optionally behind Phase 10 nginx); `.env.example`
- [ ] Tests: pytest (auth stub, RBAC 403s, tool endpoints, progress) + vitest (key components)
- [ ] Extend `.github/workflows/ci.yml` (ruff + pytest + npm build/test); `README.md` + `docs/portal.md`

### Phase 11 verification
- [ ] Login (stub in CI / real OAuth local) → `/me` with permissions
- [ ] Viewer blocked from admin CRUD; permission grant unlocks endpoint + UI
- [ ] Lesson completes + persists; try-it hits only lab target
- [ ] Launcher JSON matches CLI; target control allowlist-only, non-admin 403
- [ ] Docs render; report draft saves + exports
- [ ] `run_headers` vs portal scores high; CORS/CSRF enforced; CI green
