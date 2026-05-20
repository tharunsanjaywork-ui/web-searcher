"""
SearchMind — Firebase Memory Layer
Persistent cross-session memory with per-user data isolation using Firestore.
Replaces ChromaDB with Firebase Firestore for cloud-native storage.
"""

import json
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MESSAGES_COLLECTION = "chat_messages"


def _get_db():
    """Get Firestore client from shared config."""
    from firebase_config import get_db
    return get_db()


def initialize_firebase():
    """Initialize Firebase (called from main.py at startup)."""
    from firebase_config import initialize_firebase as _init
    _init()


def save_message(session_id, user_id, role, message_text,
                 sources=None, confidence=None):
    """Save a message to Firestore with full metadata."""
    try:
        db = _get_db()
        if db is None:
            return False

        message_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        doc_data = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": message_text,
            "timestamp": timestamp,
            "sources": json.dumps(sources) if sources else "[]",
            "confidence": confidence if confidence else "",
        }

        db.collection(MESSAGES_COLLECTION).document(message_id).set(doc_data)
        return True
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
        return False


def get_session_history(session_id, user_id):
    """Return all messages for a session filtered by user_id."""
    try:
        db = _get_db()
        if db is None:
            return []

        query = (
            db.collection(MESSAGES_COLLECTION)
            .where("session_id", "==", session_id)
            .where("user_id", "==", user_id)
        )
        docs = list(query.stream())

        if not docs:
            return []

        messages = []
        for doc in docs:
            data = doc.to_dict()
            messages.append({
                "id": doc.id,
                "role": data.get("role", "user"),
                "content": data.get("content", ""),
                "timestamp": data.get("timestamp", ""),
                "sources": _parse_sources(data.get("sources", "[]")),
                "confidence": data.get("confidence", ""),
            })

        messages.sort(key=lambda m: m["timestamp"])
        return messages
    except Exception as e:
        logger.error(f"Failed to get session history: {e}")
        return []


def _parse_sources(sources_str):
    """Safely parse JSON sources string."""
    try:
        if not sources_str:
            return []
        return json.loads(sources_str)
    except (json.JSONDecodeError, TypeError):
        return []


def get_memory_context(session_id, user_id, query):
    """Get recent conversation context from this session.
    
    Uses last 5 messages instead of semantic search since Firestore
    does not support vector similarity queries natively.
    """
    try:
        db = _get_db()
        if db is None:
            return ""

        q = (
            db.collection(MESSAGES_COLLECTION)
            .where("session_id", "==", session_id)
            .where("user_id", "==", user_id)
        )
        docs = list(q.stream())

        if not docs:
            return ""

        # Sort by timestamp and take last 5 for context
        docs.sort(key=lambda d: d.to_dict().get("timestamp", ""))
        recent = docs[-5:]

        context_parts = []
        for doc in recent:
            data = doc.to_dict()
            role = data.get("role", "unknown")
            content = data.get("content", "")
            context_parts.append(f"[{role}]: {content}")

        return "\n".join(context_parts)
    except Exception as e:
        logger.error(f"Failed to get memory context: {e}")
        return ""


def get_all_sessions(user_id):
    """Return all sessions for a specific user with preview text."""
    try:
        db = _get_db()
        if db is None:
            return []

        query = (
            db.collection(MESSAGES_COLLECTION)
            .where("user_id", "==", user_id)
        )
        docs = query.stream()

        session_map = {}
        for doc in docs:
            data = doc.to_dict()
            sid = data.get("session_id", "")
            timestamp = data.get("timestamp", "")
            role = data.get("role", "user")
            content = data.get("content", "")

            if sid not in session_map:
                session_map[sid] = {
                    "session_id": sid,
                    "preview": "",
                    "timestamp": "",
                }

            # Use the earliest user message as session preview
            if role == "user":
                existing_ts = session_map[sid]["timestamp"]
                if not existing_ts or timestamp < existing_ts:
                    preview = content[:40] if content else "New chat"
                    session_map[sid]["preview"] = preview
                    session_map[sid]["timestamp"] = timestamp

        sessions = list(session_map.values())
        for s in sessions:
            if not s["preview"]:
                s["preview"] = "New chat"

        sessions.sort(key=lambda s: s["timestamp"], reverse=True)
        return sessions
    except Exception as e:
        logger.error(f"Failed to get all sessions: {e}")
        return []
