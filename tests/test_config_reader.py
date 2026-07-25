"""Tests for the read-only static config scanner.

Uses the ``temp_config_file`` fixture so nothing is written outside
pytest's tmp_path.
"""

from ai_red_team_lab import config_reader

ENV_WITH_SECRETS = (
    "SECRET_KEY=hardcoded-secret-key-123\n"
    "ADMIN_PASSWORD=admin123\n"
    "DB_HOST=localhost\n"
    "# a comment line\n"
    "PASSWORD_FROM_ENV=${DB_PASSWORD}\n"
)

COMPOSE_SNIPPET = (
    "services:\n"
    "  web:\n"
    "    environment:\n"
    "      - FLASK_DEBUG=1\n"
    "    ports:\n"
    '      - "5000:5000"\n'
)


def _by_category(findings):
    out = {}
    for f in findings:
        out.setdefault(f["category"], []).append(f)
    return out


def test_env_secrets_flagged_high_and_redacted(temp_config_file):
    path = temp_config_file(ENV_WITH_SECRETS, name="app.env")
    result = config_reader.read_config(path)
    secrets = _by_category(result["findings"]).get("secret", [])

    high = {f["key"]: f for f in secrets if f["severity"] == "HIGH"}
    assert "SECRET_KEY" in high
    assert "ADMIN_PASSWORD" in high
    # The literal secret value must never appear in evidence.
    for f in high.values():
        assert "<redacted" in f["evidence"]
        assert "admin123" not in f["evidence"]
        assert "hardcoded-secret-key-123" not in f["evidence"]


def test_env_reference_is_info_not_high(temp_config_file):
    path = temp_config_file(ENV_WITH_SECRETS, name="app.env")
    result = config_reader.read_config(path)
    refs = [f for f in result["findings"] if f["key"] == "PASSWORD_FROM_ENV"]

    assert refs and refs[0]["severity"] == "INFO"


def test_compose_debug_and_exposed_port(temp_config_file):
    path = temp_config_file(COMPOSE_SNIPPET, name="docker-compose.yml")
    result = config_reader.read_config(path)
    cats = _by_category(result["findings"])

    assert any(f["category"] == "debug" for f in result["findings"])
    ports = cats.get("exposed_port", [])
    assert ports and ports[0]["key"] == "5000:5000"


def test_clean_file_has_zero_findings(temp_config_file):
    path = temp_config_file("NAME=app\nVERSION=1.0\n", name="clean.env")
    result = config_reader.read_config(path)

    assert result["findings"] == []
    assert result["error"] is None


def test_missing_file_reports_error(tmp_path):
    result = config_reader.read_config(tmp_path / "does-not-exist.env")

    assert result["error"] is not None
    assert result["findings"] == []
