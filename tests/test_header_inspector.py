"""Tests for the read-only security-header inspector (no network)."""

from ai_red_team_lab import header_inspector
from ai_red_team_lab.header_inspector import SECURITY_HEADERS


def test_all_absent_scores_zero():
    result = header_inspector.inspect({})

    assert result["score"] == 0
    assert result["max_score"] == 9
    assert len(result["missing"]) == 9
    assert result["present"] == []


def test_all_present_scores_nine():
    headers = {name: "some-policy" for name in SECURITY_HEADERS}
    result = header_inspector.inspect(headers)

    assert result["score"] == 9
    assert result["missing"] == []


def test_header_lookup_is_case_insensitive():
    result = header_inspector.inspect({"Content-Security-Policy": "default-src 'self'"})

    assert result["score"] == 1
    assert any(h["header"] == "content-security-policy" for h in result["present"])


def test_empty_header_value_counts_as_missing():
    result = header_inspector.inspect({"x-frame-options": "   "})

    assert result["score"] == 0


def test_insecure_cookie_flags_all_three_attributes():
    result = header_inspector.inspect({"Set-Cookie": "sid=1"})

    assert len(result["cookie_issues"]) == 3


def test_hardened_cookie_has_no_issues():
    result = header_inspector.inspect(
        {"Set-Cookie": "sid=1; Secure; HttpOnly; SameSite=Lax"}
    )

    assert result["cookie_issues"] == []
