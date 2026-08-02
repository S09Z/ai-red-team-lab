"""Hardened Flask application — the defensive counterpart of the lab target.

Same 16 routes / same feature set as ``targets/flask-app``, but every one of
the vulnerable app's 8 flaw classes is closed:

  SQLi        -> parameterized queries
  IDOR        -> ownership + auth checks
  XSS         -> Jinja autoescape (no ``| safe``) + CSP
  weak JWT    -> env secret, short expiry, ``is_admin`` re-checked from the DB
  open redir  -> relative-path allowlist for ``next``
  data expo   -> hashed passwords, minimized API fields, ``/debug`` removed
  misconfig   -> DEBUG off, secure cookies, security headers
  no CSRF     -> Flask-WTF CSRF tokens on state-changing forms

Built with an app factory so tests can drive ``create_app().test_client()``.
"""

from __future__ import annotations

import os
import secrets as secrets_mod
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import jwt
from config import Config
from database import get_db, seed
from flask import (
    Flask,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
)
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from security import register_security
from werkzeug.security import check_password_hash, generate_password_hash

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)


def create_app(testing: bool = False, database: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    if database is not None:
        app.config["DATABASE"] = database
    if testing:
        app.config["TESTING"] = True
        # Disable CSRF/rate limits so tests can exercise the routes directly;
        # the secure cookie flags and headers stay on so they can be asserted.
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["RATELIMIT_ENABLED"] = False

    # Secrets come from the environment. Fall back to an ephemeral random value
    # (never a committed literal) so a misconfigured deploy fails closed.
    app.secret_key = os.environ.get("SECRET_KEY") or secrets_mod.token_hex(32)
    app.config["JWT_SECRET"] = os.environ.get("JWT_SECRET") or secrets_mod.token_hex(32)

    register_security(app)
    csrf.init_app(app)
    limiter.init_app(app)

    _configure_cors(app)

    with app.app_context():
        seed(app.config["DATABASE"])

    _register_routes(app)
    return app


def _configure_cors(app: Flask) -> None:
    origins = [o.strip() for o in app.config["CORS_ALLOWED_ORIGINS"].split(",") if o.strip()]
    # Explicit allowlist only — never a wildcard. Empty list = no cross-origin.
    CORS(app, origins=origins, supports_credentials=True)


# ── helpers ──────────────────────────────────────────────────────────────────

def _db():
    return get_db(current_app.config["DATABASE"])


def _uid():
    return session.get("user_id")


def _is_safe_next(target: str) -> bool:
    """True only for same-site relative paths ("/foo") — blocks open redirects."""
    if not target:
        return False
    parts = urlsplit(target)
    # Reject anything with a scheme or host, and protocol-relative "//evil".
    return not parts.scheme and not parts.netloc and target.startswith("/") \
        and not target.startswith("//")


# ── routes (16) ──────────────────────────────────────────────────────────────

def _register_routes(app: Flask) -> None:  # noqa: C901 — mirrors the 16-route target

    # 1 — index
    @app.route("/")
    def index():
        return render_template("index.html")

    # 2 — login ── FIX: parameterized query + hashed-password verification
    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit(lambda: current_app.config["LOGIN_RATELIMIT"])
    def login():
        error = None
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            db = _db()
            row = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            db.close()
            if row and check_password_hash(row["password_hash"], password):
                session.clear()
                session["user_id"] = row["id"]
                session["username"] = row["username"]
                session["is_admin"] = row["is_admin"]
                return redirect("/dashboard")
            error = "Invalid credentials"
        return render_template("login.html", error=error)

    # 3 — logout
    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        return redirect("/")

    # 4 — dashboard (requires login)
    @app.route("/dashboard")
    def dashboard():
        if not _uid():
            return redirect("/login")
        db = _db()
        posts = db.execute(
            "SELECT posts.*, users.username FROM posts "
            "JOIN users ON posts.user_id = users.id "
            "ORDER BY created_at DESC"
        ).fetchall()
        db.close()
        return render_template("dashboard.html", posts=posts)

    # 5 — profile GET (public fields only; no email/PII leak)
    @app.route("/profile/<int:user_id>")
    def profile(user_id):
        if not _uid():
            return redirect("/login")
        db = _db()
        user = db.execute(
            "SELECT id, username, bio FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        db.close()
        if not user:
            return "User not found", 404
        return render_template("profile.html", user=user, owner=(user_id == _uid()))

    # 6 — profile update ── FIX: ownership check (IDOR) + autoescaped bio
    @app.route("/profile/<int:user_id>/update", methods=["POST"])
    def profile_update(user_id):
        if not _uid():
            return redirect("/login")
        if user_id != _uid():
            return "Forbidden", 403
        bio = request.form.get("bio", "")
        db = _db()
        db.execute("UPDATE users SET bio = ? WHERE id = ?", (bio, user_id))
        db.commit()
        db.close()
        return redirect(f"/profile/{user_id}")

    # 7 — search ── FIX: parameterized (already) + autoescaped reflection
    @app.route("/search")
    def search():
        q = request.args.get("q", "")
        db = _db()
        results = db.execute(
            "SELECT * FROM posts WHERE title LIKE ?", (f"%{q}%",)
        ).fetchall()
        db.close()
        return render_template("search.html", q=q, results=results)

    # 8 — new post (requires login; content autoescaped on render)
    @app.route("/post/new", methods=["POST"])
    def post_new():
        if not _uid():
            return redirect("/login")
        db = _db()
        db.execute(
            "INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
            (_uid(), request.form.get("title", ""), request.form.get("content", "")),
        )
        db.commit()
        db.close()
        return redirect("/dashboard")

    # 9 — view post ── FIX: content autoescaped (no ``| safe``)
    @app.route("/post/<int:post_id>")
    def post_view(post_id):
        db = _db()
        post = db.execute(
            "SELECT * FROM posts WHERE id = ?", (post_id,)
        ).fetchone()
        db.close()
        if not post:
            return "Not found", 404
        return render_template("post.html", post=post)

    # 10 — admin panel ── FIX: re-verify admin against the DB
    @app.route("/admin")
    def admin():
        if not _current_user_is_admin():
            return "Forbidden", 403
        db = _db()
        users = db.execute(
            "SELECT id, username, email, is_admin FROM users"
        ).fetchall()
        db.close()
        return render_template("admin.html", users=users)

    # 11 — admin reset password ── FIX: admin re-check + hashed write
    @app.route("/admin/reset-password", methods=["POST"])
    def admin_reset_password():
        if not _current_user_is_admin():
            return "Forbidden", 403
        user_id = request.form.get("user_id")
        new_password = request.form.get("new_password", "")
        if not new_password:
            return "Password required", 400
        db = _db()
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new_password), user_id),
        )
        db.commit()
        db.close()
        return redirect("/admin")

    # 12 — redirect ── FIX: relative-path allowlist for ``next``
    @app.route("/redirect")
    def safe_redirect():
        target = request.args.get("next", "/")
        return redirect(target if _is_safe_next(target) else "/")

    # 13 — API list users ── FIX: auth required, no password/PII in payload
    @app.route("/api/users")
    def api_users():
        if not _uid():
            return jsonify({"error": "authentication required"}), 401
        db = _db()
        rows = db.execute("SELECT id, username FROM users").fetchall()
        db.close()
        return jsonify([dict(r) for r in rows])

    # 14 — API get user ── FIX: auth required, minimized fields
    @app.route("/api/user/<int:user_id>")
    def api_user(user_id):
        if not _uid():
            return jsonify({"error": "authentication required"}), 401
        db = _db()
        row = db.execute(
            "SELECT id, username, bio FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        db.close()
        if not row:
            return jsonify({"error": "not found"}), 404
        return jsonify(dict(row))

    # 15 — API issue JWT ── FIX: env secret, password verified, short expiry
    @app.route("/api/token", methods=["POST"])
    @csrf.exempt
    @limiter.limit(lambda: current_app.config["JWT_RATELIMIT"])
    def api_token():
        data = request.get_json(silent=True) or {}
        username = data.get("username") or request.form.get("username", "")
        password = data.get("password") or request.form.get("password", "")
        db = _db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        db.close()
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "invalid credentials"}), 401
        now = datetime.now(timezone.utc)
        # ``sub`` only — callers must re-check authorization against the DB
        # rather than trusting an embedded ``is_admin`` claim.
        token = jwt.encode(
            {
                "sub": user["username"],
                "iat": now,
                "exp": now + timedelta(seconds=current_app.config["JWT_EXPIRY_SECONDS"]),
            },
            current_app.config["JWT_SECRET"],
            algorithm=current_app.config["JWT_ALGORITHM"],
        )
        return jsonify({"token": token})

    # 16 — ``/debug`` is intentionally NOT defined -> 404 (was a config dump).


def _current_user_is_admin() -> bool:
    """Re-verify the current session's admin status from the database."""
    if not _uid():
        return False
    db = _db()
    row = db.execute("SELECT is_admin FROM users WHERE id = ?", (_uid(),)).fetchone()
    db.close()
    return bool(row and row["is_admin"])


if __name__ == "__main__":
    # Dev entry point only; production uses gunicorn (see Dockerfile).
    create_app().run(host="127.0.0.1", port=5001)
