#!/usr/bin/env python3
"""CLI wrapper for the TCP connect scanner (ai_red_team_lab.port_enumerator).

Classifies each TCP port on a host as open, closed, or filtered using plain
stdlib socket connects — no raw sockets, no payloads, nothing modified
(CLAUDE.md §2 — Recon Lead). Ports accept comma-separated values and ranges,
e.g. --ports 5000 or --ports 22,80,443 or --ports 1-1024.

    python tools/run_ports.py --host localhost --ports 5000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai_red_team_lab import port_enumerator  # noqa: E402


def parse_ports(spec: str) -> list[int]:
    """Expand a "5000", "22,80,443", or "1-1024" spec into a list of ints."""
    ports: list[int] = []
    for token in spec.replace(" ", ",").split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start, end = token.split("-", 1)
            ports.extend(range(int(start), int(end) + 1))
        else:
            ports.append(int(token))
    return ports


def main() -> int:
    p = argparse.ArgumentParser(description="Read-only TCP connect port scanner.")
    p.add_argument("--host", required=True, help="Target host.")
    p.add_argument(
        "--ports", required=True, help="Ports: '5000', '22,80,443', or '1-1024'."
    )
    p.add_argument(
        "--timeout", type=float, default=1.0, help="Per-port timeout in seconds."
    )
    p.add_argument("--json", action="store_true", help="Emit the raw JSON result.")
    args = p.parse_args()

    try:
        ports = parse_ports(args.ports)
    except ValueError as exc:
        print(f"ERROR   invalid --ports value: {exc}")
        return 1
    if not ports:
        print("ERROR   no ports parsed from --ports")
        return 1

    result = port_enumerator.scan(args.host, ports, timeout=args.timeout)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Host     : {result['host']}")
    print(f"Elapsed  : {result['elapsed_ms']} ms")
    print(f"Open     : {result['open']}")
    print(f"Closed   : {result['closed']}")
    print(f"Filtered : {result['filtered']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
