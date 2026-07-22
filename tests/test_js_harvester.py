"""Tests for the read-only JavaScript harvester.

HTTP is intercepted by ``mocked_responses`` (no real network). Verifies
script extraction, following external ``src``, and that known secret /
endpoint / storage strings are matched with no false negatives.
"""

from ai_red_team_lab import js_harvester

PAGE_HTML = (
    "<html><head>"
    '<script src="/static/app.js"></script>'
    "<script>var inline = 1;</script>"
    "</head><body>hi</body></html>"
)
APP_JS = (
    'const API_BASE = "http://localhost:5000";\n'
    '// DEV_TOKEN = "dev-abc123"\n'
    'fetch("/api/users").then(r => r.json());\n'
    'localStorage.setItem("session_token", "xyz");\n'
)


def _register(mocked_responses):
    mocked_responses.get("http://target/", body=PAGE_HTML)
    mocked_responses.get("http://target/static/app.js", body=APP_JS)


def test_external_script_is_followed(mocked_responses):
    _register(mocked_responses)
    result = js_harvester.harvest("http://target/")

    externals = [s for s in result["scripts"] if s["type"] == "external"]
    assert any(s["src"] == "http://target/static/app.js" for s in externals)
    assert result["error"] is None


def test_known_strings_are_matched(mocked_responses):
    _register(mocked_responses)
    result = js_harvester.harvest("http://target/")
    categories = {f["category"] for f in result["findings"]}

    assert "endpoint" in categories      # /api/users
    assert "storage" in categories       # localStorage.setItem
    assert "secret" in categories        # DEV_TOKEN = "..."
    assert "dev_comment" in categories   # DEV
    assert len(result["findings"]) >= 2


def test_endpoint_match_value(mocked_responses):
    _register(mocked_responses)
    result = js_harvester.harvest("http://target/")
    endpoints = [f["match"] for f in result["findings"] if f["category"] == "endpoint"]

    assert any("/api/users" in m for m in endpoints)


def test_custom_patterns_override_defaults(mocked_responses):
    _register(mocked_responses)
    result = js_harvester.harvest("http://target/", patterns={"base": r"API_BASE"})
    categories = {f["category"] for f in result["findings"]}

    assert categories == {"base"}


def test_page_fetch_error_is_captured(mocked_responses):
    import requests

    mocked_responses.get(
        "http://target/", body=requests.exceptions.ConnectionError("boom")
    )
    result = js_harvester.harvest("http://target/")

    assert result["error"] is not None
    assert result["findings"] == []


# --- Phase 3b security-hardening tests: SSRF guard ---

def test_link_local_script_src_is_blocked(mocked_responses):
    # 169.254.169.254 is the AWS instance-metadata endpoint (link-local).
    page = '<html><script src="http://169.254.169.254/latest/meta-data/"></script></html>'
    mocked_responses.get("http://target/", body=page)
    result = js_harvester.harvest("http://target/")

    blocked = [s for s in result["scripts"] if "blocked" in (s.get("error") or "")]
    assert len(blocked) == 1
    assert blocked[0]["src"] == "http://169.254.169.254/latest/meta-data/"
    assert blocked[0]["chars"] == 0


def test_loopback_script_src_is_blocked(mocked_responses):
    page = '<html><script src="http://127.0.0.1:8080/internal.js"></script></html>'
    mocked_responses.get("http://target/", body=page)
    result = js_harvester.harvest("http://target/")

    blocked = [s for s in result["scripts"] if "blocked" in (s.get("error") or "")]
    assert len(blocked) == 1
    assert "127.0.0.1" in blocked[0]["src"]


def test_normal_external_script_src_is_allowed(mocked_responses):
    page = '<html><script src="http://cdn.example.com/lib.js"></script></html>'
    mocked_responses.get("http://target/", body=page)
    mocked_responses.get("http://cdn.example.com/lib.js", body="var x = 1;")
    result = js_harvester.harvest("http://target/")

    allowed = [s for s in result["scripts"] if s.get("error") is None]
    assert len(allowed) == 1
    assert allowed[0]["src"] == "http://cdn.example.com/lib.js"
