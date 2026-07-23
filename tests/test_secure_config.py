"""The hardened config carries no hardcoded secrets.

``config_reader`` reports HIGH findings for the vulnerable app's
``config.py`` (SECRET_KEY, JWT_SECRET literals). The secure config keeps
secrets in the environment, so the same scan yields 0 HIGH.
"""

from pathlib import Path

from ai_red_team_lab import config_reader

SECURE_CONFIG = (
    Path(__file__).resolve().parents[1]
    / "targets"
    / "flask-app-secure"
    / "config.py"
)


def test_secure_config_has_no_high_findings():
    result = config_reader.read_config(SECURE_CONFIG)

    assert result["error"] is None
    high = [f for f in result["findings"] if f["severity"] == "HIGH"]
    assert high == []


def test_secure_config_has_no_debug_enabled_finding():
    result = config_reader.read_config(SECURE_CONFIG)

    assert [f for f in result["findings"] if f["category"] == "debug"] == []
