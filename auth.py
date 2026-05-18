"""
SearchMind — Authentication Module
Simple email/password auth with JWT tokens and JSON file storage.
"""

import os
import json
import hashlib
import secrets
import logging
from datetime import datetime, timezone
import jwt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))


def _load_users():
    """Load users from JSON file."""
    try:
        if not os.path.exists(USERS_FILE):
            return {}
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load users: {e}")
        return {}


def _save_users(users):
    """Save users to JSON file."""
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save users: {e}")


def _hash_password(password, salt=None):
    """Hash password with SHA-256 and salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return salt, hashed


def register(email, password):
    """Register a new user. Returns (data, error)."""
    try:
        users = _load_users()
        email = email.strip().lower()

        if email in users:
            return None, "Email already registered"

        if len(password) < 6:
            return None, "Password must be at least 6 characters"

        salt, hashed = _hash_password(password)
        user_id = secrets.token_hex(8)

        users[email] = {
            "user_id": user_id,
            "salt": salt,
            "password_hash": hashed,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _save_users(users)

        token = _create_token(user_id, email)
        return {"token": token, "user_id": user_id, "email": email}, None
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return None, "Registration failed"


def login(email, password):
    """Login user. Returns (data, error)."""
    try:
        users = _load_users()
        email = email.strip().lower()

        if email not in users:
            return None, "Invalid email or password"

        user = users[email]
        _, hashed = _hash_password(password, user["salt"])

        if hashed != user["password_hash"]:
            return None, "Invalid email or password"

        token = _create_token(user["user_id"], email)
        return {"token": token, "user_id": user["user_id"], "email": email}, None
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return None, "Login failed"


def _create_token(user_id, email):
    """Create JWT token."""
    payload = {"user_id": user_id, "email": email}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_token(token):
    """Verify JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        return None
