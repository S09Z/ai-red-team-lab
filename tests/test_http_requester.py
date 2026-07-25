"""Tests for the read-only HTTP requester.

All HTTP is intercepted by the ``mocked_responses`` fixture, so no request
ever leaves the machine; unregistered calls raise ConnectionError.
"""

import requests

from ai_red_team_lab import http_requester
from ai_red_team_lab.http_requester import BODY_EXCERPT_LIMIT


def test_basic_response_is_summarized(mocked_responses):
    mocked_responses.get(
        "http://target/",
        status=200,
        body="hello",
        headers={"X-Lab-Marker": "yes"},
    )
    result = http_requester.fetch("http://target/")

    assert result["status_code"] == 200
    assert result["response_headers"]["X-Lab-Marker"] == "yes"
    assert result["response_body_excerpt"] == "hello"
    assert result["redirect_chain"] == []
    assert result["error"] is None
    assert isinstance(result["elapsed_ms"], float)


def test_body_excerpt_is_capped_at_2000_chars(mocked_responses):
    mocked_responses.get("http://target/big", status=200, body="A" * 5000)
    result = http_requester.fetch("http://target/big")

    assert len(result["response_body_excerpt"]) == BODY_EXCERPT_LIMIT == 2000


def test_redirect_chain_is_recorded(mocked_responses):
    mocked_responses.get(
        "http://target/a", status=302, headers={"Location": "http://target/b"}
    )
    mocked_responses.get("http://target/b", status=200, body="done")
    result = http_requester.fetch("http://target/a")

    assert result["status_code"] == 200
    assert len(result["redirect_chain"]) == 1
    assert result["redirect_chain"][0]["status_code"] == 302
    assert result["redirect_chain"][0]["location"] == "http://target/b"


def test_no_follow_redirects_stops_at_first_hop(mocked_responses):
    mocked_responses.get(
        "http://target/a", status=302, headers={"Location": "http://target/b"}
    )
    result = http_requester.fetch("http://target/a", follow_redirects=False)

    assert result["status_code"] == 302
    assert result["redirect_chain"] == []


def test_connection_error_is_captured_not_raised(mocked_responses):
    mocked_responses.get(
        "http://target/down", body=requests.exceptions.ConnectionError("refused")
    )
    result = http_requester.fetch("http://target/down")

    assert result["status_code"] is None
    assert result["error"] is not None
    assert "ConnectionError" in result["error"]
