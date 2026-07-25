"""Tests for the read-only TCP connect enumerator.

Uses a loopback listener for the "open" case (no external network) and
monkeypatches ``socket.create_connection`` to deterministically exercise the
"closed" and "filtered" branches.
"""

import socket

from ai_red_team_lab import port_enumerator


def test_open_port_detected_on_loopback():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    port = listener.getsockname()[1]
    try:
        result = port_enumerator.scan("127.0.0.1", [port], timeout=1.0)
    finally:
        listener.close()

    assert result["open"] == [port]
    assert result["closed"] == []
    assert result["filtered"] == []
    assert isinstance(result["elapsed_ms"], float)


def test_refused_connection_is_closed(monkeypatch):
    def refuse(*args, **kwargs):
        raise ConnectionRefusedError()

    monkeypatch.setattr(port_enumerator.socket, "create_connection", refuse)
    result = port_enumerator.scan("127.0.0.1", [9999], timeout=0.5)

    assert result["closed"] == [9999]
    assert result["open"] == []


def test_timeout_is_filtered(monkeypatch):
    def time_out(*args, **kwargs):
        raise socket.timeout()

    monkeypatch.setattr(port_enumerator.socket, "create_connection", time_out)
    result = port_enumerator.scan("127.0.0.1", [9998], timeout=0.5)

    assert result["filtered"] == [9998]
    assert result["open"] == []


def test_results_are_sorted(monkeypatch):
    monkeypatch.setattr(
        port_enumerator.socket,
        "create_connection",
        lambda *a, **k: (_ for _ in ()).throw(ConnectionRefusedError()),
    )
    result = port_enumerator.scan("127.0.0.1", [30, 10, 20], timeout=0.5)

    assert result["closed"] == [10, 20, 30]
