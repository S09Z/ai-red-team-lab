"""Read-only JavaScript harvesting.

Fetches a page, extracts ``<script>`` tags with BeautifulSoup, optionally
follows external script ``src`` URLs, and statically scans the script text
for endpoints, secret-like tokens, developer comments, and client-side
storage usage. Scripts are parsed as text and NEVER executed (CLAUDE.md §5 —
JavaScript Analyst); the target is not modified.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

MATCH_EXCERPT_LIMIT = 120

# Category -> regex. Kept deliberately simple: these surface *candidates*
# for a human to validate, not confirmed findings.
DEFAULT_PATTERNS: dict[str, str] = {
    "endpoint": r"/api/[\w\-/]+",
    "secret": r"(?i)[\w-]*(?:token|secret|password|passwd|pwd|api[_-]?key|key)"
    r"[\w-]*\s*[:=]\s*['\"]?[^\s'\";,]+",
    "dev_comment": r"(?i)\b(?:TODO|FIXME|DEV|HACK|XXX)\b",
    "storage": r"(?i)(?:local|session)Storage\.(?:get|set|remove)Item",
}


def harvest(
    url: str,
    patterns: dict[str, str] | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Harvest and statically scan the scripts referenced by ``url``.

    Returns a dict with:
      - ``scripts``   list of {type: inline|external, src, chars}
      - ``findings``  list of {category, source, line, match}
      - ``error``     None, or "ExceptionType: message" if the page fetch failed
    """
    patterns = patterns or DEFAULT_PATTERNS
    result: dict[str, Any] = {
        "url": url,
        "scripts": [],
        "findings": [],
        "error": None,
    }

    try:
        page = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    soup = BeautifulSoup(page.text, "html.parser")

    # Collect (source_label, script_text) pairs, following external src.
    sources: list[tuple[str, str]] = []
    for tag in soup.find_all("script"):
        src = tag.get("src")
        if src:
            script_url = urljoin(url, src)
            try:
                text = requests.get(script_url, timeout=timeout).text
            except requests.RequestException as exc:
                result["scripts"].append(
                    {"type": "external", "src": script_url, "chars": 0, "error": str(exc)}
                )
                continue
            result["scripts"].append(
                {"type": "external", "src": script_url, "chars": len(text)}
            )
            sources.append((script_url, text))
        else:
            text = tag.string or tag.get_text() or ""
            result["scripts"].append(
                {"type": "inline", "src": None, "chars": len(text)}
            )
            sources.append((f"{url}#inline-script", text))

    compiled = {category: re.compile(pat) for category, pat in patterns.items()}
    for source_label, text in sources:
        for category, rx in compiled.items():
            for match in rx.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                snippet = match.group(0).strip()[:MATCH_EXCERPT_LIMIT]
                result["findings"].append(
                    {
                        "category": category,
                        "source": source_label,
                        "line": line,
                        "match": snippet,
                    }
                )

    return result
