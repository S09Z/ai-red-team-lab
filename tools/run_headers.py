#!/usr/bin/env python3
"""CLI wrapper for the security-header audit (ai_red_team_lab.header_inspector).

Fetches a URL once (via http_requester) and scores its security headers 0-9,
listing what is present, what is missing, and any insecure cookie attributes.
Read-only analysis of observed headers (CLAUDE.md §2).

    python tools/run_headers.py --url http://localhost:5000/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai_red_team_lab import header_inspector, http_requester  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Read-only security-header audit.")
    p.add_argument("--url", required=True, help="Target URL to audit.")
    p.add_argument("--timeout", type=float, default=10.0, help="Timeout in seconds.")
    p.add_argument("--json", action="store_true", help="Emit the raw JSON result.")
    args = p.parse_args()

    response = http_requester.fetch(url=args.url, timeout=args.timeout)
    if response["error"]:
        print(f"ERROR   {response['error']}")
        return 1

    audit = header_inspector.inspect(response["response_headers"])

    if args.json:
        print(json.dumps(audit, indent=2))
        return 0

    print(f"URL   : {args.url}")
    print(f"Score : {audit['score']}/{audit['max_score']} security headers present")
    if audit["present"]:
        print("Present:")
        for item in audit["present"]:
            print(f"  + {item['header']}")
    if audit["missing"]:
        print("Missing:")
        for item in audit["missing"]:
            print(f"  - {item['header']}  ({item['rationale']})")
    if audit["cookie_issues"]:
        print("Cookie issues:")
        for issue in audit["cookie_issues"]:
            print(f"  ! {issue}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
