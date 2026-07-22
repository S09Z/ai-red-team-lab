"""Shared pytest fixtures for the observation-library test suite.

These fixtures enforce the read-only posture required by CLAUDE.md §2:
tests exercise the observation tools without making real network calls
and without writing anywhere outside pytest's ``tmp_path``.
"""

import pytest
import responses


@pytest.fixture
def mocked_responses():
    """Intercept all outbound HTTP through the ``responses`` library.

    Requests to URLs that were not explicitly registered raise a
    ``ConnectionError``, which guarantees the suite never touches the
    real network. Register expected calls inside the test, e.g.::

        def test_fetch(mocked_responses):
            mocked_responses.get("http://target/", body="ok", status=200)
            ...
    """
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def temp_config_file(tmp_path):
    """Return a factory that writes text to a temp file and yields its path.

    Used by config-reader tests to scan sample ``.env`` / compose content
    without planting fixtures on the real filesystem::

        def test_reads_secret(temp_config_file):
            path = temp_config_file("SECRET_KEY=abc123\n")
            ...
    """

    def _write(content: str, name: str = "sample.env"):
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        return path

    return _write
