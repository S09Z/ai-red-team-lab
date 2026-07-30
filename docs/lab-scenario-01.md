# Lab Scenario 01 — Blog Platform Assessment

A guided first assessment against the bundled Flask target. Work through it in
role order, gathering evidence before conclusions. The answer key at the
bottom is **spoiler-hidden** — try to derive findings from observation first.

## Scenario

You are the red team on an **authorized** assessment of an internal blog
platform the owner runs locally. They want to know its security posture before
any wider rollout. You have been given the running app and its source; you may
observe and review, but you may not exploit or modify anything.

## Scope

- **In scope:**
  - The running target at `http://localhost:5000`
  - The application source under `targets/flask-app/`
  - The deployment config: `docker-compose.yml`, `targets/flask-app/Dockerfile`
- **Out of scope:** anything else on your host, the Docker daemon itself, the
  public internet. If you find a reference that leads outside this scope, flag
  it — do not follow it (CLAUDE.md §1).

## Setup

Follow [setup.md](setup.md): `docker compose up -d`, confirm `healthy`.

## Suggested role order

Follow the [workflow](workflow.md); a good order for this target:

1. **Recon Lead** — port + root-page observation
2. **Application Mapper** — walk pages and forms
3. **API Analyst** — inventory `/api/*`
4. **JavaScript Analyst** — harvest client scripts
5. **Secure Code Reviewer** — read the route handlers + templates
6. **Infrastructure Reviewer** — scan `docker-compose.yml` and `config.py`
7. **Threat Modeling Lead** — assemble trust boundaries and abuse cases
8. **Risk Analyst** — rate each hypothesis
9. **Report Writer** — assemble with the templates

## Starter commands

```bash
python tools/run_ports.py   --host localhost --ports 5000
python tools/run_http.py    --url http://localhost:5000/            --json
python tools/run_headers.py --url http://localhost:5000/
python tools/run_js.py      --url http://localhost:5000/
python tools/run_http.py    --url http://localhost:5000/api/users   --json
python tools/run_config.py  --file docker-compose.yml
python tools/run_config.py  --file targets/flask-app/config.py
```

## Success criteria

You have completed the scenario when your report:

- [ ] Names the technology stack with the **evidence** that identified it
- [ ] Inventories the reachable pages and API endpoints (method, auth, params)
- [ ] Identifies the trust boundaries (unauth → auth, client → server, app → DB)
- [ ] Produces at least **6 findings**, each with all 8 evidence fields
      ([`finding-card.md`](../templates/finding-card.md))
- [ ] Assigns a **justified** confidence to each finding (no inflation)
- [ ] Recommends a **non-destructive** validation for every finding
- [ ] Lists remaining unknowns and questions for the owner
- [ ] Passes every box in [`role-checklist.md`](../templates/role-checklist.md)

The goal is not to "find them all" — it is to justify every claim with
evidence gathered this session and never to exploit.

---

## Answer key (spoilers)

> Open only after your own pass. This is lab-authoring material — the intended
> weaknesses built into the target. In a real assessment you would derive
> these from evidence, not from a key.

<details>
<summary>Show the 8 intended vulnerability classes (16 routes)</summary>

The target is deliberately vulnerable. Intended issues, by route:

| # | Route | Class | Note |
|---|---|---|---|
| 2 | `POST /login` | **SQL injection** | f-string interpolation into the SQL query; `admin'--` bypasses the password check |
| 5 | `GET /profile/<id>` | **IDOR** | any logged-in user can view any profile — no ownership check |
| 6 | `POST /profile/<id>/update` | **IDOR + stored XSS** | overwrite any user's `bio`; bio rendered raw |
| 7 | `GET /search?q=` | **Reflected XSS** | `q` rendered with `\| safe` |
| 8/9 | `POST /post/new`, `GET /post/<id>` | **Stored XSS** | content stored unsanitized, rendered with `\| safe` |
| 10 | `GET /admin` | **Broken access control** | trusts a session flag set at login (reachable via the SQLi bypass) |
| 11 | `POST /admin/reset-password` | **No CSRF + IDOR** | resets any user's password by `user_id` param |
| 12 | `GET /redirect?next=` | **Open redirect** | `next` not validated → phishing |
| 13 | `GET /api/users` | **Sensitive data exposure** | returns plaintext passwords, unauthenticated |
| 14 | `GET /api/user/<id>` | **IDOR** | no authentication required |
| 15 | `POST /api/token` | **Broken auth (weak JWT)** | secret is `supersecret`; `is_admin` claim trusted without DB re-check |
| 16 | `GET /debug` | **Debug/info exposure** | dumps env vars, config secrets, and session data |

Supporting config issues to surface via `run_config.py` / header review:
- `DEBUG=True`, weak/hardcoded `SECRET_KEY` and `JWT_SECRET` in `config.py`
- Missing security headers (score 0/9) and insecure session-cookie attributes
- Host-exposed port `5000:5000` in `docker-compose.yml`

</details>
