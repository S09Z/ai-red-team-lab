"""SQLite setup and seed data for the lab target.

Plaintext passwords, fake API keys, and a pre-seeded XSS payload are
intentional — they exist so the observation tooling has real findings to
surface during a training session.
"""

import sqlite3

import config


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def seed() -> None:
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            email    TEXT,
            bio      TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS posts (
            id         INTEGER PRIMARY KEY,
            user_id    INTEGER REFERENCES users(id),
            title      TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS secrets (
            id    INTEGER PRIMARY KEY,
            name  TEXT NOT NULL,
            value TEXT NOT NULL
        );
    """)

    # Plaintext passwords — intentional lab misconfiguration.
    conn.execute(
        "INSERT OR IGNORE INTO users (id, username, password, is_admin, email) "
        "VALUES (1, 'admin', 'admin123', 1, 'admin@lab.local')"
    )
    conn.execute(
        "INSERT OR IGNORE INTO users (id, username, password, is_admin, email) "
        "VALUES (2, 'alice', 'password', 0, 'alice@lab.local')"
    )
    conn.execute(
        "INSERT OR IGNORE INTO users (id, username, password, is_admin, email) "
        "VALUES (3, 'bob', 'bob123', 0, 'bob@lab.local')"
    )

    conn.execute(
        "INSERT OR IGNORE INTO posts (id, user_id, title, content) "
        "VALUES (1, 1, 'Welcome', 'Admin welcome post.')"
    )
    conn.execute(
        "INSERT OR IGNORE INTO posts (id, user_id, title, content) "
        "VALUES (2, 2, 'Hello World', 'Post from alice.')"
    )
    # Pre-seeded stored-XSS payload so the lab has an immediate finding.
    conn.execute(
        "INSERT OR IGNORE INTO posts (id, user_id, title, content) "
        r"VALUES (3, 3, 'XSS Demo', '<img src=x onerror=""alert(1)"">')"
    )

    # Fake secrets — surfaced by config_reader and js_harvester during training.
    conn.execute(
        "INSERT OR IGNORE INTO secrets (id, name, value) "
        "VALUES (1, 'stripe_api_key', 'sk_live_fake_1234567890abcdef')"
    )
    conn.execute(
        "INSERT OR IGNORE INTO secrets (id, name, value) "
        "VALUES (2, 'aws_access_key', 'AKIAIOSFODNN7EXAMPLE')"
    )
    conn.execute(
        "INSERT OR IGNORE INTO secrets (id, name, value) "
        "VALUES (3, 'internal_api_key', 'int-key-9f8e7d6c5b4a3b2a1c0d')"
    )

    conn.commit()
    conn.close()
