"""Read-only TCP connect enumeration.

Uses only the standard-library ``socket`` module — no raw sockets, no
elevated privileges. Each port is probed with a plain TCP connect and the
socket is closed immediately; no payload is ever sent and nothing is
modified (CLAUDE.md §2 — read-only; Recon Lead tooling).
"""

from __future__ import annotations

import socket
import time
from typing import Any, Iterable


def scan(host: str, ports: Iterable[int], timeout: float = 1.0) -> dict[str, Any]:
    """Classify each TCP port on ``host`` as open, closed, or filtered.

    - ``open``     connection succeeded (and was immediately closed)
    - ``closed``   connection actively refused
    - ``filtered`` timed out or otherwise unreachable (no response)

    Returns: ``open``, ``closed``, ``filtered`` (sorted int lists) and
    ``elapsed_ms``.
    """
    open_ports: list[int] = []
    closed_ports: list[int] = []
    filtered_ports: list[int] = []

    start = time.perf_counter()
    for port in ports:
        try:
            conn = socket.create_connection((host, port), timeout=timeout)
        except ConnectionRefusedError:
            closed_ports.append(port)
        except (socket.timeout, TimeoutError):
            filtered_ports.append(port)
        except OSError:
            # No route to host, DNS failure, reset, etc. — treated as filtered.
            filtered_ports.append(port)
        else:
            open_ports.append(port)
            conn.close()

    return {
        "host": host,
        "open": sorted(open_ports),
        "closed": sorted(closed_ports),
        "filtered": sorted(filtered_ports),
        "elapsed_ms": round((time.perf_counter() - start) * 1000, 1),
    }
