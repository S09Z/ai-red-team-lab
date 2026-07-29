# Observation Tools

Thin command-line wrappers around the read-only observation library
(`src/ai_red_team_lab/`). Each tool performs **one** kind of observation and
prints an evidence-friendly summary; pass `--json` on any of them for the raw
structured result to paste into a finding card.

These tools are **read-only** and stay within the lab's hard safety
constraints (CLAUDE.md §2): they observe, fingerprint, and statically scan.
They never exploit, modify, brute-force, or execute target code. Findings are
*candidates for validation*, not confirmed vulnerabilities.

## Requirements

- Python 3.11+
- The library's runtime deps: `requests`, `beautifulsoup4` (installed via
  `poetry install`). The runners themselves are stdlib-only and add
  `src/` to `sys.path`, so they work without installing the package.

## Tools

| Tool | Observes | Key flags | Library |
|---|---|---|---|
| `run_http.py` | One HTTP request/response | `--url` `--method` `--no-redirects` `--timeout` | `http_requester` |
| `run_headers.py` | Security-header score (0–9) + cookie flags | `--url` `--timeout` | `header_inspector` |
| `run_js.py` | Scripts + endpoint/secret/comment/storage candidates | `--url` `--timeout` | `js_harvester` |
| `run_config.py` | Secrets, debug flags, exposed ports in a config file | `--file` | `config_reader` |
| `run_ports.py` | TCP open/closed/filtered | `--host` `--ports` `--timeout` | `port_enumerator` |

Every tool also accepts `--json`.

## Examples

```bash
# HTTP observation
python tools/run_http.py --url http://localhost:5000/

# Security-header audit (fetches, then scores)
python tools/run_headers.py --url http://localhost:5000/

# Harvest and statically scan client-side JavaScript
python tools/run_js.py --url http://localhost:5000/

# Static scan of a config file (secrets redacted in output)
python tools/run_config.py --file docker-compose.yml

# TCP connect scan — single port, list, or range
python tools/run_ports.py --host localhost --ports 5000
python tools/run_ports.py --host localhost --ports 22,80,443
python tools/run_ports.py --host localhost --ports 1-1024
```

## Exit codes

`0` on success. `1` when the underlying observation reports an `error`
(e.g. connection failure, unreadable file) — the error is printed to stdout.
