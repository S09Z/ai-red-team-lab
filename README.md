# AI Red Team Lab

A self-contained, **read-only** lab for practicing evidence-driven security
assessment with an AI red team. It pairs a deliberately vulnerable target with
observation tooling and a strict governance model, so you can learn to gather
evidence, reason about risk, and write findings **without ever exploiting or
modifying** the target.

> ⚠️ **Authorized training only.** The bundled target is intentionally
> insecure. Run it only on the isolated local network Docker Compose creates;
> never expose it to the internet or point the tooling at systems you do not
> own. All work here is defensive and observation-first — see
> [`CLAUDE.md`](CLAUDE.md).

## What's in the box

- **A vulnerable target** — a Flask blog app (`targets/flask-app/`) with 8
  vulnerability classes across 16 routes, run in an isolated container.
- **A read-only observation library** (`src/ai_red_team_lab/`) — HTTP
  observation, TCP connect scanning, JavaScript harvesting, security-header
  auditing, and static config scanning. Nothing exploits or writes.
- **CLI runners** (`tools/`) — thin, stdlib-only wrappers to gather evidence
  from the shell, each with `--json` output.
- **Report templates** (`templates/`) — an 8-field finding card, a 12-section
  report skeleton, and a pre-report self-verification checklist.
- **Governance** (`CLAUDE.md`) — the binding rules an AI (or human) assessor
  follows: observe first, never exploit, justify every conclusion with
  evidence from this session.

## Quick start

```bash
# 1. Install dependencies (runtime + dev/test)
poetry install --with dev

# 2. Start the target (isolated network, port 5000 only)
docker compose up -d
docker compose ps            # wait for STATUS: healthy

# 3. Gather your first evidence
python tools/run_http.py    --url http://localhost:5000/
python tools/run_headers.py --url http://localhost:5000/
python tools/run_config.py  --file targets/flask-app/config.py

# 4. Tear down when done
docker compose down
```

Full instructions and troubleshooting are in [docs/setup.md](docs/setup.md).

## Documentation

| Doc | What it covers |
|---|---|
| [docs/setup.md](docs/setup.md) | Prerequisites, install, starting the target, first run |
| [docs/workflow.md](docs/workflow.md) | A full assessment session mapped to the Observe→Report loop |
| [docs/roles.md](docs/roles.md) | Each red-team role: trigger, tools, output, boundaries |
| [docs/lab-scenario-01.md](docs/lab-scenario-01.md) | Guided first assessment with success criteria (answer key hidden) |
| [tools/README.md](tools/README.md) | The CLI observation tools and their flags |
| [CLAUDE.md](CLAUDE.md) | The governance model — safety constraints, roles, evidence rules |

## Repository layout

```
src/ai_red_team_lab/   read-only observation library
tools/                 CLI runners over the library
templates/             finding card, full report, self-check
targets/flask-app/     deliberately vulnerable target
docs/                  setup, workflow, roles, scenario
tests/                 pytest suite for the library
docker-compose.yml     runs the target on an isolated network
CLAUDE.md              governance / operating rules
```

## Development

```bash
poetry run pytest -q          # run the test suite
poetry run ruff check .       # lint
```

## Safety model (summary)

The assessor operates observation-first and never modifies, exploits, brute-
forces, persists, escalates, or reaches the internet from within the
assessment. Every finding traces to evidence gathered *this session* and
recommends only non-destructive validation. The full, binding rules are in
[`CLAUDE.md`](CLAUDE.md).
