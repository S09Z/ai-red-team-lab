#!/usr/bin/env python3
"""CLI wrapper for the JavaScript harvester (ai_red_team_lab.js_harvester).

Fetches a page, extracts its scripts, and statically scans them for endpoint,
secret-like, developer-comment, and client-storage *candidates*. Scripts are
parsed as text and NEVER executed (CLAUDE.md §5 — JavaScript Analyst).
Findings are candidates for human validation, not confirmed issues.

    python tools/run_js.py --url http://localhost:5000/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai_red_team_lab import js_harvester  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Read-only JavaScript harvester.")
    p.add_argument("--url", required=True, help="Page URL to harvest scripts from.")
    p.add_argument("--timeout", type=float, default=10.0, help="Timeout in seconds.")
    p.add_argument("--json", action="store_true", help="Emit the raw JSON result.")
    args = p.parse_args()

    result = js_harvester.harvest(url=args.url, timeout=args.timeout)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["error"] is None else 1

    if result["error"]:
        print(f"ERROR   {result['error']}")
        return 1

    print(f"URL     : {args.url}")
    print(f"Scripts : {len(result['scripts'])}")
    print(f"Findings: {len(result['findings'])} candidate(s) for validation")
    for f in result["findings"]:
        print(f"  [{f['category']}] {f['source']}:{f['line']}  {f['match']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
