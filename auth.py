"""
SearchMind — Authentication Module
Email/password auth with JWT tokens and Firebase Firestore storage.
Uses bcrypt for password hashing (replaces SHA-256).
"""

import os
import logging
import secrets
from datetime import datetime, timezone
import jwt
import bcrypt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY must be at least 32 characters long. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

USERS_COLLECTION = "users"


def _get_db():
    """Get Firestore client from shared config."""
    from firebase_config import get_db
    return get_db()


def _hash_password(password):
    """Hash password using bcrypt."""
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def _verify_password(password, hashed):
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(
        password.encode("utf-8"), hashed.encode("utf-8")
    )


def register(email, password):
    """Register a new user in Firestore. Returns (data, error)."""
    try:
        db = _get_db()
        email = email.strip().lower()

        # Check if user already exists
        doc = db.collection(USERS_COLLECTION).document(email).get()
        if doc.exists:
            return None, "Email already registered"

        if len(password) < 6:
            return None, "Password must be at least 6 characters"

        user_id = secrets.token_hex(8)
        password_hash = _hash_password(password)

        db.collection(USERS_COLLECTION).document(email).set({
            "user_id": user_id,
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        token = _create_token(user_id, email)
        return {"token": token, "user_id": user_id, "email": email}, None
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return None, "Registration failed"


def login(email, password):
    """Login user from Firestore. Returns (data, error)."""
    try:
        db = _get_db()
        email = email.strip().lower()

        doc = db.collection(USERS_COLLECTION).document(email).get()
        if not doc.exists:
            return None, "Invalid email or password"

        user_data = doc.to_dict()
        if not _verify_password(password, user_data["password_hash"]):
            return None, "Invalid email or password"

        token = _create_token(user_data["user_id"], email)
        return {
            "token": token,
            "user_id": user_data["user_id"],
            "email": email,
        }, None
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
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        logger.error(f"Token verification unexpected error: {e}")
        return None
