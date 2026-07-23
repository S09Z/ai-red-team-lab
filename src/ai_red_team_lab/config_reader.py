"""Read-only static configuration scan.

Reads a config file (``.env``, docker-compose, YAML, etc.) from disk and
flags hardcoded secrets, debug flags, and host-exposed ports by simple line
matching. Read-only: it opens the file and writes nothing (CLAUDE.md §5 —
Infrastructure Reviewer / Secure Code Reviewer).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

VALUE_EXCERPT_LIMIT = 80

# A key whose name contains one of these words, assigned a concrete value,
# is treated as a hardcoded secret.
SECRET_ASSIGN_RE = re.compile(
    r"(?i)([\w-]*(?:secret|password|passwd|pwd|token|api[_-]?key|key)[\w-]*)"
    r"\s*[:=]\s*(.+)$"
)
DEBUG_RE = re.compile(r"(?i)\b(?:flask_)?debug\b\s*[:=]\s*(true|1|on|yes)\b")
# Compose-style host:container mapping as the line's main content.
PORT_MAP_RE = re.compile(r"^-?\s*['\"]?(\d{2,5}):(\d{2,5})['\"]?$")


def read_config(path) -> dict[str, Any]:
    """Statically scan ``path`` for secrets, debug flags, and exposed ports.

    Returns a dict with:
      - ``findings``  list of {line, category, severity, key, evidence, recommendation}
      - ``error``     None, or "ExceptionType: message" if the file is unreadable
    """
    file_path = Path(path)
    result: dict[str, Any] = {"path": str(file_path), "findings": [], "error": None}

    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        finding = _scan_line(lineno, stripped)
        if finding:
            result["findings"].append(finding)

    return result


def _scan_line(lineno: int, line: str) -> dict[str, Any] | None:
    debug_match = DEBUG_RE.search(line)
    if debug_match:
        return {
            "line": lineno,
            "category": "debug",
            "severity": "MEDIUM",
            "key": "DEBUG",
            "evidence": line[:VALUE_EXCERPT_LIMIT],
            "recommendation": "Disable debug mode in any shared or production config.",
        }

    port_match = PORT_MAP_RE.match(line)
    if port_match:
        return {
            "line": lineno,
            "category": "exposed_port",
            "severity": "LOW",
            "key": f"{port_match.group(1)}:{port_match.group(2)}",
            "evidence": line[:VALUE_EXCERPT_LIMIT],
            "recommendation": "Confirm the host port must be exposed; bind to localhost if not.",
        }

    secret_match = SECRET_ASSIGN_RE.search(line)
    if secret_match:
        key, value = secret_match.group(1), secret_match.group(2).strip().strip("'\"")
        if not value:
            return None
        # A value delegated to an env/secret reference is not a hardcoded secret.
        if value.startswith("$") or value.startswith("${"):
            severity = "INFO"
            recommendation = "Value is a reference; confirm the source is not itself committed."
        else:
            severity = "HIGH"
            recommendation = "Remove the hardcoded secret; load it from a secret manager or env var."
        return {
            "line": lineno,
            "category": "secret",
            "severity": severity,
            "key": key,
            "evidence": f"{key}=<redacted:{len(value)} chars>",
            "recommendation": recommendation,
        }

    return None
