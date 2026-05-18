"""
SearchMind — ChromaDB Memory Layer
Persistent cross-session memory with per-user data isolation.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

_chroma_client = None
_collection = None


def initialize_chroma_client():
    """Create persistent ChromaDB client and collection."""
    global _chroma_client, _collection
    try:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _chroma_client.get_or_create_collection(
            name="chat_messages"
        )
        logger.info(f"ChromaDB initialized at {CHROMA_PATH}")
        return _collection
    except Exception as e:
        logger.error(f"ChromaDB initialization failed: {e}")
        return None


def _get_collection():
    """Get or initialize the ChromaDB collection."""
    global _collection
    if _collection is None:
        initialize_chroma_client()
    return _collection


def save_message(session_id, user_id, role, message_text,
                 sources=None, confidence=None):
    """Save a message with user_id for per-user isolation."""
    try:
        collection = _get_collection()
        if collection is None:
            return False

        message_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        metadata = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "timestamp": timestamp,
            "sources": json.dumps(sources) if sources else "[]",
            "confidence": confidence if confidence else "",
        }

        collection.add(
            ids=[message_id],
            documents=[message_text],
            metadatas=[metadata]
        )
        return True
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
        return False


def get_session_history(session_id, user_id):
    """Return all messages for a session filtered by user_id."""
    try:
        collection = _get_collection()
        if collection is None:
            return []

        results = collection.get(
            where={"$and": [
                {"session_id": session_id},
                {"user_id": user_id}
            ]},
            include=["documents", "metadatas"]
        )

        if not results or not results.get("ids"):
            return []

        messages = []
        for i, doc_id in enumerate(results["ids"]):
            meta = results["metadatas"][i]
            doc = results["documents"][i]
            messages.append({
                "id": doc_id,
                "role": meta.get("role", "user"),
                "content": doc,
                "timestamp": meta.get("timestamp", ""),
                "sources": _parse_sources(meta.get("sources", "[]")),
                "confidence": meta.get("confidence", ""),
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
    """Semantic search for top 5 relevant past messages for this user."""
    try:
        collection = _get_collection()
        if collection is None:
            return ""

        count = collection.count()
        if count == 0:
            return ""

        results = collection.query(
            query_texts=[query],
            where={"$and": [
                {"session_id": session_id},
                {"user_id": user_id}
            ]},
            n_results=min(5, count),
            include=["documents", "metadatas"]
        )

        if not results or not results.get("documents"):
            return ""

        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []

        if not docs:
            return ""

        context_parts = []
        for i, doc in enumerate(docs):
            role = metas[i].get("role", "unknown") if i < len(metas) else "unknown"
            context_parts.append(f"[{role}]: {doc}")

        return "\n".join(context_parts)
    except Exception as e:
        logger.error(f"Failed to get memory context: {e}")
        return ""


def get_all_sessions(user_id):
    """Return all sessions for a specific user only."""
    try:
        collection = _get_collection()
        if collection is None:
            return []

        all_data = collection.get(
            where={"user_id": user_id},
            include=["documents", "metadatas"]
        )

        if not all_data or not all_data.get("ids"):
            return []

        session_map = {}
        for i, doc_id in enumerate(all_data["ids"]):
            meta = all_data["metadatas"][i]
            doc = all_data["documents"][i]
            sid = meta.get("session_id", "")
            timestamp = meta.get("timestamp", "")
            role = meta.get("role", "user")

            if sid not in session_map:
                session_map[sid] = {
                    "session_id": sid,
                    "preview": "",
                    "timestamp": "",
                }

            if role == "user":
                existing_ts = session_map[sid]["timestamp"]
                if not existing_ts or timestamp < existing_ts:
                    preview = doc[:40] if doc else "New chat"
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
