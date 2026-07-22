# AI Red Team Lab — Build TODO

## Phase 1 · Foundation
- [x] `pyproject.toml` — add description, fix author, add deps (`requests`, `beautifulsoup4`, `rich`, `click`) and dev deps (`pytest`, `pytest-cov`, `responses`, `flask`)
- [x] `src/ai_red_team_lab/__init__.py`
- [x] `tests/__init__.py`
- [x] `tests/conftest.py` — mock HTTP server fixture + temp config file fixture

## Phase 2 · Observation Library
- [ ] `src/ai_red_team_lab/http_requester.py` — `fetch()` → status, headers, body excerpt, redirect chain
- [ ] `src/ai_red_team_lab/port_enumerator.py` — `scan()` → open/closed/filtered via stdlib `socket` only
- [ ] `src/ai_red_team_lab/js_harvester.py` — `harvest()` → extract scripts, scan for secrets/endpoints/comments
- [ ] `src/ai_red_team_lab/header_inspector.py` — `inspect()` → audit 9 security headers, return score 0–9
- [ ] `src/ai_red_team_lab/config_reader.py` — `read_config()` → static scan of compose/.env/yaml for secrets/debug flags

## Phase 3 · Tests
- [ ] `tests/test_http_requester.py`
- [ ] `tests/test_port_enumerator.py`
- [ ] `tests/test_js_harvester.py`
- [ ] `tests/test_header_inspector.py`
- [ ] `tests/test_config_reader.py`

## Phase 4 · Flask Target
- [ ] `targets/flask-app/config.py` — hardcoded secrets, DEBUG=True, insecure cookie flags, CSRF disabled
- [ ] `targets/flask-app/database.py` — SQLite seed: users (plaintext passwords), posts, secrets (fake API key)
- [ ] `targets/flask-app/app.py` — 16 vulnerable routes (SQLi, IDOR, XSS, broken auth, open redirect, etc.)
- [ ] `targets/flask-app/static/app.js` — hardcoded API_BASE, dev token comment, insecure localStorage
- [ ] `targets/flask-app/templates/` — base, index, login, dashboard, profile, admin
- [ ] `targets/flask-app/requirements.txt` — `flask`, `pyjwt`
- [ ] `targets/flask-app/Dockerfile`

## Phase 5 · Docker Compose
- [ ] `docker-compose.yml` — flask-app service, port 5000, isolated bridge network, healthcheck

## Phase 6 · Templates
- [ ] `templates/finding-card.md` — 8-field evidence card (CLAUDE.md §6)
- [ ] `templates/full-report.md` — 12-section report skeleton (CLAUDE.md §8)
- [ ] `templates/role-checklist.md` — self-verification checklist (CLAUDE.md §10)

## Phase 7 · CLI Tools
- [ ] `tools/README.md`
- [ ] `tools/run_http.py`
- [ ] `tools/run_ports.py`
- [ ] `tools/run_js.py`
- [ ] `tools/run_headers.py`
- [ ] `tools/run_config.py`

## Phase 8 · Docs
- [ ] `docs/setup.md` — prereqs, install, first run
- [ ] `docs/workflow.md` — full assessment session walkthrough
- [ ] `docs/roles.md` — role → trigger phrase → tools → output → restrictions
- [ ] `docs/lab-scenario-01.md` — scope, role order, success criteria, spoiler-hidden findings

## Phase 9 · README
- [ ] `README.md` — quick-start, what the lab is, links to docs

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
