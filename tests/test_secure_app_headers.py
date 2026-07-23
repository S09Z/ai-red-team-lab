"""Header/cookie posture of the hardened target, scored by the same inspector.

Drives ``create_app().test_client()`` and feeds real responses into
``ai_red_team_lab.header_inspector`` — the vulnerable target scores 0/9 here,
the hardened one scores 9/9 with no cookie issues.
"""

import sys
from pathlib import Path

import pytest

# The secure app mirrors the vulnerable app's flat layout (bare ``import
# config`` etc.), so put its directory on the path — same idiom the CLI tools
# use to reach ``src/``.
SECURE_APP_DIR = Path(__file__).resolve().parents[1] / "targets" / "flask-app-secure"
sys.path.insert(0, str(SECURE_APP_DIR))

from app import create_app  # noqa: E402  (path must be set first)

from ai_red_team_lab import header_inspector  # noqa: E402


@pytest.fixture
def client(tmp_path):
    app = create_app(testing=True, database=str(tmp_path / "secure.db"))
    return app.test_client()


def test_index_scores_nine_of_nine(client):
    resp = client.get("/")
    result = header_inspector.inspect(dict(resp.headers))

    assert result["score"] == 9
    assert result["missing"] == []


def test_login_sets_secure_cookie(client):
    # A successful login sets the session cookie; it must carry all three
    # protective attributes (Secure, HttpOnly, SameSite).
    resp = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    result = header_inspector.inspect(dict(resp.headers))

    assert result["cookie_issues"] == []
