"""
SearchMind — Firebase Configuration
Shared Firebase Admin SDK initialization for Firestore.
"""

import os
import json
import base64
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_db = None
_initialized = False


def clean_private_key(key_str: str) -> str:
    """Normalize and format a PEM private key, ensuring proper header, footer, and wrapping."""
    if not key_str or not isinstance(key_str, str):
        return key_str

    # Strip surrounding quotes and whitespace
    key_str = key_str.strip().strip("'\"").strip()

    # Normalize newlines (replace literal "\n" strings with actual newlines)
    key_str = key_str.replace("\\n", "\n").replace("\\\\n", "\n")

    # If the key doesn't have standard headers, try wrapping it
    header = "-----BEGIN PRIVATE KEY-----"
    footer = "-----END PRIVATE KEY-----"

    if header not in key_str:
        # Wrap it if raw base64 string
        key_str = f"{header}\n{key_str}\n{footer}"

    try:
        # Extract base64 content between headers
        start_idx = key_str.index(header) + len(header)
        end_idx = key_str.index(footer)
        content = key_str[start_idx:end_idx].strip()

        # Remove any non-base64 characters except for whitespace/newlines
        # Base64 chars are A-Z, a-z, 0-9, +, /, =, and whitespace
        cleaned_chars = []
        for char in content:
            if char.isalnum() or char in ('+', '/', '=', '\n', '\r'):
                cleaned_chars.append(char)
            elif char in (' ', '\t'):
                # Treat spaces/tabs inside the base64 content as newlines (frequently collapsed on env load)
                cleaned_chars.append('\n')

        cleaned_content = "".join(cleaned_chars)

        # Remove all whitespaces/newlines to get a continuous base64 string
        base64_only = "".join(c for c in cleaned_content if c not in ('\n', '\r', ' ', '\t'))

        # Standard PEM wrapping: 64 characters per line
        wrapped_lines = [base64_only[i:i+64] for i in range(0, len(base64_only), 64)]

        # Reconstruct the PEM key perfectly
        reconstructed = f"{header}\n" + "\n".join(wrapped_lines) + f"\n{footer}\n"
        return reconstructed
    except Exception as e:
        logger.warning(f"Failed to fully reconstruct private key: {e}. Returning simple normalized string.")
        return key_str


def initialize_firebase():
    """Initialize Firebase Admin SDK and return Firestore client."""
    global _db, _initialized

    if _initialized:
        return _db

    try:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
        cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON", "")

        # Fallback list of common local credential file names in root
        default_paths = [
            "firebase-service-account.json.json",
            "firebase-service-account.json"
        ]

        if not cred_path and not cred_json:
            for path in default_paths:
                if os.path.exists(path):
                    cred_path = path
                    break

        cred_data = None

        if cred_path and os.path.exists(cred_path):
            try:
                with open(cred_path, "r", encoding="utf-8") as f:
                    cred_data = json.load(f, strict=False)
            except Exception as e:
                logger.error(f"Failed to read/parse local credential JSON from {cred_path}: {e}")
                # Fallback to path string if json parsing fails
                cred_data = cred_path
        elif cred_json:
            cred_json_clean = cred_json.strip().strip("'\"").strip()
            b64_err = None
            raw_err = None

            # 1. Try to decode as Base64 JSON
            try:
                missing_padding = len(cred_json_clean) % 4
                if missing_padding:
                    cred_json_clean += '=' * (4 - missing_padding)
                
                decoded_bytes = base64.b64decode(cred_json_clean)
                cred_data = json.loads(decoded_bytes.decode('utf-8'), strict=False)
            except Exception as e:
                b64_err = e

            # 2. Try to parse as raw JSON directly
            if cred_data is None:
                try:
                    cred_data = json.loads(cred_json, strict=False)
                except Exception as e:
                    raw_err = e

            if cred_data is None:
                raise RuntimeError(
                    f"Failed to parse FIREBASE_CREDENTIALS_JSON. "
                    f"Base64 parsing error: {b64_err}. "
                    f"Raw JSON parsing error: {raw_err}."
                )

        if cred_data is None:
            raise RuntimeError(
                "Firebase credentials not configured. "
                "Ensure firebase-service-account.json is in the root directory "
                "or set FIREBASE_CREDENTIALS_PATH / FIREBASE_CREDENTIALS_JSON in your environment."
            )

        # Sanitize private key if we have a parsed dictionary
        if isinstance(cred_data, dict):
            if "private_key" in cred_data and isinstance(cred_data["private_key"], str):
                cred_data["private_key"] = clean_private_key(cred_data["private_key"])
            cred = credentials.Certificate(cred_data)
        else:
            # Fallback to file path string if not a dictionary
            cred = credentials.Certificate(cred_data)

        firebase_admin.initialize_app(cred)
        _db = firestore.client()
        _initialized = True
        logger.info("Firebase Firestore initialized successfully")
        return _db
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        raise


def get_db():
    """Get Firestore client, initializing if needed."""
    global _db
    if _db is None:
        initialize_firebase()
    return _db
