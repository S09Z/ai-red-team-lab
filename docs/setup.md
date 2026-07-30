# Setup

How to stand up the lab and run your first observation. Everything here is
local and read-only — nothing in this repo reaches the public internet.

## Prerequisites

- **Docker** + **Docker Compose v2** (`docker compose version`)
- **Python 3.11+** (`python3 --version`)
- **Poetry** (for the dev/test workflow; optional if you only run the tools)

## 1. Install Python dependencies

The observation library needs `requests` and `beautifulsoup4`; the dev group
adds `pytest`, `ruff`, and `flask`.

```bash
poetry install --with dev
```

The CLI runners in `tools/` are stdlib-only and add `src/` to `sys.path`
themselves, so they work even before the package is installed — but the
library's runtime deps (`requests`, `beautifulsoup4`) must be importable.

## 2. Start the target

The deliberately vulnerable Flask app runs in an isolated bridge network and
publishes only port 5000 to your host.

```bash
docker compose up -d
docker compose ps        # STATUS should become healthy within ~15s
```

> ⚠️ The target is intentionally insecure. Run it **only** on the isolated
> lab network Compose creates. Never expose it beyond localhost.

## 3. First observation

With the target healthy, confirm the tooling works end to end:

```bash
python tools/run_http.py    --url http://localhost:5000/
python tools/run_headers.py --url http://localhost:5000/
python tools/run_js.py      --url http://localhost:5000/
python tools/run_config.py  --file docker-compose.yml
python tools/run_ports.py   --host localhost --ports 5000
```

Each tool prints an evidence-friendly summary; add `--json` for the raw
structured result to paste into a finding card (`templates/finding-card.md`).

## 4. Run the tests

```bash
poetry run pytest -q          # or: python3 -m pytest tests/ -q
poetry run ruff check .
```

## Teardown

```bash
docker compose down          # stop and remove the container + network
```

## Troubleshooting

- **Port 5000 already in use** (common on macOS — AirPlay Receiver binds it):
  disable AirPlay Receiver in System Settings, or remap the host side in
  `docker-compose.yml` (e.g. `"5001:5000"`) and adjust the `--url`.
- **`ModuleNotFoundError: ai_red_team_lab`** when importing directly: run the
  tools from the repo root, or use `poetry run` / pytest which set the path.
- **Target not `healthy`**: check `docker compose logs flask-app`.

Next: read [workflow.md](workflow.md) for how a full assessment session runs.
