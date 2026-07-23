#!/usr/bin/env python3
"""CLI wrapper for the static config scanner (ai_red_team_lab.config_reader).

Reads a config file from disk (.env, docker-compose, YAML, etc.) and flags
hardcoded secrets, debug flags, and host-exposed ports by line matching.
Read-only: the file is opened and nothing is written (CLAUDE.md §5 —
Infrastructure Reviewer). Secret values are redacted in the output.

    python tools/run_config.py --file docker-compose.yml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai_red_team_lab import config_reader  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Read-only static config scanner.")
    p.add_argument("--file", required=True, help="Path to the config file to scan.")
    p.add_argument("--json", action="store_true", help="Emit the raw JSON result.")
    args = p.parse_args()

    result = config_reader.read_config(args.file)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["error"] is None else 1

    if result["error"]:
        print(f"ERROR   {result['error']}")
        return 1

    findings = result["findings"]
    print(f"File     : {result['path']}")
    print(f"Findings : {len(findings)}")
    for f in findings:
        print(
            f"  [{f['severity']}] line {f['line']} ({f['category']}): "
            f"{f['evidence']}"
        )
        print(f"           fix: {f['recommendation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
