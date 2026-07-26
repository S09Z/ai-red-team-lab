# Deliberately insecure configuration — lab target only.
SECRET_KEY = "hardcoded-dev-secret-key-do-not-use-in-prod"
JWT_SECRET = "supersecret"
JWT_ALGORITHM = "HS256"
DATABASE = "lab.db"
DEBUG = True

# Insecure session-cookie flags (missing Secure, HttpOnly, SameSite).
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = None
