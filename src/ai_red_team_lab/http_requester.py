"""Read-only HTTP observation.

Issues a single HTTP request and returns a structured, evidence-friendly
summary of the response. It observes one request/response exchange; it does
not exploit, brute-force, or modify the target (CLAUDE.md §2 — read-only;
Recon Lead / Application Mapper tooling).
"""

from __future__ import annotations

import time
from typing import Any

import requests

BODY_EXCERPT_LIMIT = 2000


def fetch(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    cookies: dict | None = None,
    body: str | bytes | None = None,
    follow_redirects: bool = True,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Perform one HTTP request and summarize the response.

    Returns a dict with:
      - ``status_code``           final response status (int) or None on error
      - ``response_headers``      response headers as a plain dict
      - ``response_body_excerpt`` first ``BODY_EXCERPT_LIMIT`` chars of the body
      - ``redirect_chain``        list of hops: {status_code, url, location}
      - ``elapsed_ms``            wall-clock time for the exchange
      - ``error``                 None, or "ExceptionType: message" on failure

    On failure every field except ``error`` keeps its empty/None default.
    """
    result: dict[str, Any] = {
        "url": url,
        "method": method.upper(),
        "status_code": None,
        "response_headers": {},
        "response_body_excerpt": "",
        "redirect_chain": [],
        "elapsed_ms": None,
        "error": None,
    }

    start = time.perf_counter()
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            cookies=cookies,
            data=body,
            allow_redirects=follow_redirects,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        result["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 1)
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    result["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 1)
    result["status_code"] = response.status_code
    result["response_headers"] = dict(response.headers)
    result["response_body_excerpt"] = response.text[:BODY_EXCERPT_LIMIT]
    result["redirect_chain"] = [
        {
            "status_code": hop.status_code,
            "url": hop.url,
            "location": hop.headers.get("Location"),
        }
        for hop in response.history
    ]
    return result
