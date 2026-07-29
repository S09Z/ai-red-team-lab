#!/usr/bin/env python3
"""CLI wrapper for the read-only HTTP observer (ai_red_team_lab.http_requester).

Issues a single request and prints an evidence-friendly summary of the
response. Read-only: one request/response exchange, no exploitation
(CLAUDE.md §2). Use --json for the raw structured result.

    python tools/run_http.py --url http://localhost:5000/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai_red_team_lab import http_requester  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Read-only HTTP request observer.")
    p.add_argument("--url", required=True, help="Target URL to observe.")
    p.add_argument("--method", default="GET", help="HTTP method (default: GET).")
    p.add_argument(
        "--no-redirects", action="store_true", help="Do not follow redirects."
    )
    p.add_argument("--timeout", type=float, default=10.0, help="Timeout in seconds.")
    p.add_argument("--json", action="store_true", help="Emit the raw JSON result.")
    args = p.parse_args()

    result = http_requester.fetch(
        url=args.url,
        method=args.method,
        follow_redirects=not args.no_redirects,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["error"] is None else 1

    if result["error"]:
        print(f"ERROR   {result['error']}")
        return 1

    print(f"{result['method']} {result['url']}")
    print(f"Status  : {result['status_code']}")
    print(f"Elapsed : {result['elapsed_ms']} ms")
    print(f"Headers : {len(result['response_headers'])}")
    if result["redirect_chain"]:
        print(f"Redirects ({len(result['redirect_chain'])}):")
        for hop in result["redirect_chain"]:
            print(f"  {hop['status_code']} -> {hop['location']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
