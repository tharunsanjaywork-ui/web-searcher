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

        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        elif cred_json:
            cred_json_clean = cred_json.strip().strip("'\"").strip()
            cred_data = None
            b64_err = None
            raw_err = None

            # 1. Try to decode as Base64 JSON
            try:
                # Add padding back if it was stripped
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

            cred = credentials.Certificate(cred_data)
        else:
            raise RuntimeError(
                "Firebase credentials not configured. "
                "Ensure firebase-service-account.json is in the root directory "
                "or set FIREBASE_CREDENTIALS_PATH / FIREBASE_CREDENTIALS_JSON in your environment."
            )

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
