"""SQLite setup and seed data for the hardened lab target.

Passwords are stored as **salted hashes** (``werkzeug.security``) and there is
no plaintext-secrets table — the two data-exposure fixes relative to the
vulnerable app's ``database.py``.
"""

import sqlite3

from werkzeug.security import generate_password_hash


def get_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def seed(path: str) -> None:
    conn = get_db(path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin      INTEGER DEFAULT 0,
            email         TEXT,
            bio           TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS posts (
            id         INTEGER PRIMARY KEY,
            user_id    INTEGER REFERENCES users(id),
            title      TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Same demo accounts as the vulnerable app, but passwords are hashed.
    seed_users = [
        (1, "admin", "admin123", 1, "admin@lab.local"),
        (2, "alice", "password", 0, "alice@lab.local"),
        (3, "bob", "bob123", 0, "bob@lab.local"),
    ]
    for uid, username, password, is_admin, email in seed_users:
        conn.execute(
            "INSERT OR IGNORE INTO users "
            "(id, username, password_hash, is_admin, email) VALUES (?, ?, ?, ?, ?)",
            (uid, username, generate_password_hash(password), is_admin, email),
        )

    conn.execute(
        "INSERT OR IGNORE INTO posts (id, user_id, title, content) "
        "VALUES (1, 1, 'Welcome', 'Admin welcome post.')"
    )
    conn.execute(
        "INSERT OR IGNORE INTO posts (id, user_id, title, content) "
        "VALUES (2, 2, 'Hello World', 'Post from alice.')"
    )
    # The old stored-XSS payload, kept as literal text to demonstrate that
    # Jinja autoescaping now renders it inert instead of executing it.
    conn.execute(
        "INSERT OR IGNORE INTO posts (id, user_id, title, content) "
        r"VALUES (3, 3, 'Escaping Demo', '<img src=x onerror=alert(1)>')"
    )

    conn.commit()
    conn.close()
