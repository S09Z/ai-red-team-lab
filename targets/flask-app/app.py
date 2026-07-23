"""Deliberately vulnerable Flask application — authorized lab target only.

Each route is labelled with its primary vulnerability class so the red-team
observation tooling has a concrete target to surface.  Do NOT deploy outside
the isolated lab network.

16 routes, 8 vulnerability classes:
  SQLi, IDOR, reflected XSS, stored XSS, broken auth (weak JWT),
  open redirect, sensitive data exposure, debug info exposure.
"""

import os

import jwt
from flask import Flask, jsonify, redirect, render_template, request, session

import config
from database import get_db, seed

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config.update(
    DEBUG=config.DEBUG,
    SESSION_COOKIE_SECURE=config.SESSION_COOKIE_SECURE,
    SESSION_COOKIE_HTTPONLY=config.SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_SAMESITE=config.SESSION_COOKIE_SAMESITE,
)

with app.app_context():
    seed()


# ── helpers ──────────────────────────────────────────────────────────────────

def _uid():
    return session.get("user_id")


# ── routes (16) ──────────────────────────────────────────────────────────────

# 1 — index
@app.route("/")
def index():
    return render_template("index.html")


# 2 — login (GET + POST) ── VULN: SQLi via string interpolation
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        db = get_db()
        # VULNERABLE: f-string interpolation into SQL → classic SQLi.
        # e.g. username="admin'--" bypasses password check.
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        row = db.execute(query).fetchone()
        db.close()
        if row:
            session["user_id"] = row["id"]
            session["username"] = row["username"]
            session["is_admin"] = row["is_admin"]
            return redirect("/dashboard")
        error = "Invalid credentials"
    return render_template("login.html", error=error)


# 3 — logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# 4 — dashboard (requires login)
@app.route("/dashboard")
def dashboard():
    if not _uid():
        return redirect("/login")
    db = get_db()
    posts = db.execute(
        "SELECT posts.*, users.username FROM posts "
        "JOIN users ON posts.user_id = users.id "
        "ORDER BY created_at DESC"
    ).fetchall()
    db.close()
    return render_template("dashboard.html", posts=posts)


# 5 — profile GET ── VULN: IDOR (no ownership check)
@app.route("/profile/<int:user_id>")
def profile(user_id):
    if not _uid():
        return redirect("/login")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    if not user:
        return "User not found", 404
    return render_template("profile.html", user=user)


# 6 — profile update POST ── VULN: IDOR on update; bio stored raw → stored XSS
@app.route("/profile/<int:user_id>/update", methods=["POST"])
def profile_update(user_id):
    if not _uid():
        return redirect("/login")
    # VULNERABLE: no check that user_id == session user_id → any user can
    # overwrite any other user's bio.
    bio = request.form.get("bio", "")
    db = get_db()
    db.execute("UPDATE users SET bio = ? WHERE id = ?", (bio, user_id))
    db.commit()
    db.close()
    return redirect(f"/profile/{user_id}")


# 7 — search ── VULN: reflected XSS (q rendered with | safe in template)
@app.route("/search")
def search():
    q = request.args.get("q", "")
    db = get_db()
    results = db.execute(
        "SELECT * FROM posts WHERE title LIKE ?", (f"%{q}%",)
    ).fetchall()
    db.close()
    # q is passed to the template and rendered as {{ q | safe }} → reflected XSS.
    return render_template("search.html", q=q, results=results)


# 8 — new post POST ── VULN: content stored without sanitisation → stored XSS
@app.route("/post/new", methods=["POST"])
def post_new():
    if not _uid():
        return redirect("/login")
    db = get_db()
    db.execute(
        "INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
        (_uid(), request.form.get("title", ""), request.form.get("content", "")),
    )
    db.commit()
    db.close()
    return redirect("/dashboard")


# 9 — view post ── VULN: content rendered with | safe → stored XSS execution
@app.route("/post/<int:post_id>")
def post_view(post_id):
    db = get_db()
    post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    db.close()
    if not post:
        return "Not found", 404
    return render_template("post.html", post=post)


# 10 — admin panel ── VULN: broken access control (trusts session flag set at
#      login; after SQLi bypass the flag reflects whatever the DB row says)
@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return "Forbidden", 403
    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    db.close()
    return render_template("admin.html", users=users)


# 11 — admin reset password ── VULN: no CSRF token; IDOR via user_id param
@app.route("/admin/reset-password", methods=["POST"])
def admin_reset_password():
    if not session.get("is_admin"):
        return "Forbidden", 403
    user_id = request.form.get("user_id")
    new_password = request.form.get("new_password", "newpass123")
    db = get_db()
    db.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
    db.commit()
    db.close()
    return redirect("/admin")


# 12 — open redirect ── VULN: next param not validated
@app.route("/redirect")
def open_redirect():
    # VULNERABLE: any absolute URL accepted → phishing / credential harvesting.
    return redirect(request.args.get("next", "/"))


# 13 — API: list users ── VULN: sensitive data exposure (plaintext passwords)
@app.route("/api/users")
def api_users():
    db = get_db()
    rows = db.execute(
        "SELECT id, username, password, email, is_admin FROM users"
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# 14 — API: get user by ID ── VULN: IDOR, no authentication required
@app.route("/api/user/<int:user_id>")
def api_user(user_id):
    db = get_db()
    row = db.execute(
        "SELECT id, username, email, bio FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


# 15 — API: issue JWT ── VULN: weak secret ("supersecret"); is_admin claim
#      embedded in token and trusted by callers without DB re-verification
@app.route("/api/token", methods=["POST"])
def api_token():
    data = request.get_json(silent=True) or {}
    username = data.get("username") or request.form.get("username", "")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    db.close()
    if not user:
        return jsonify({"error": "user not found"}), 404
    # VULNERABLE: JWT_SECRET is "supersecret" — trivially brute-forced.
    # The is_admin claim is embedded and trusted without DB re-check.
    token = jwt.encode(
        {"sub": username, "is_admin": user["is_admin"]},
        config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM,
    )
    return jsonify({"token": token})


# 16 — debug endpoint ── VULN: exposes env vars, config secrets, session data
@app.route("/debug")
def debug_info():
    return jsonify({
        "env": dict(os.environ),
        "config": {
            "SECRET_KEY": config.SECRET_KEY,
            "JWT_SECRET": config.JWT_SECRET,
            "DATABASE": config.DATABASE,
            "DEBUG": config.DEBUG,
        },
        "session": dict(session),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
