"""
memory.py — In-process session memory

Stores conversation history per session_id.
When you're ready to scale:
  - swap the dict for Redis (redis-py async client)
  - or SQLite (aiosqlite) for persistence across restarts

Usage in your RAG pipeline:
    history = memory.get("session-abc")
    # … retrieve docs, build prompt …
    memory.add("session-abc", "user", user_input)
    memory.add("session-abc", "assistant", model_reply)
"""

from collections import defaultdict
from app.schemas import Message


# { session_id: [Message, …] }
_store: dict[str, list[Message]] = defaultdict(list)

MAX_TURNS = 20  # keep last N turns to avoid hitting context limit


def get(session_id: str) -> list[Message]:
    """Return stored messages for a session (empty list if new)."""
    return list(_store[session_id])


def add(session_id: str, role: str, content: str) -> None:
    """Append one turn and trim to MAX_TURNS."""
    _store[session_id].append(Message(role=role, content=content))
    # Keep only system message + last MAX_TURNS non-system messages
    system = [m for m in _store[session_id] if m.role == "system"]
    non_system = [m for m in _store[session_id] if m.role != "system"]
    _store[session_id] = system + non_system[-MAX_TURNS:]


def clear(session_id: str) -> None:
    """Reset a session (useful for /reset endpoint)."""
    _store.pop(session_id, None)


def all_sessions() -> list[str]:
    return list(_store.keys())
