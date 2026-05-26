"""
schemas.py — All Pydantic models (request + response).
Centralizing them avoids circular imports and makes it easy
to version your API later (v1 schemas, v2 schemas…).
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── Input ──────────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str       # "system" | "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    max_tokens: int   = Field(default=512,  ge=1,   le=4096)
    temperature: float = Field(default=0.7,  ge=0.0, le=2.0)
    top_p: float       = Field(default=0.95, ge=0.0, le=1.0)
    stream: bool       = False

    # ── RAG fields ────────────────────────────────────────────────────────────
    # Pass retrieved text chunks from your vector store here.
    # The prompt builder injects them automatically before the conversation.
    context: Optional[str] = None

    # Future: pass a session_id to load persistent memory from DB
    session_id: Optional[str] = None


class GenerateRequest(BaseModel):
    """Backward-compatible single-turn endpoint."""
    prompt: str
    max_tokens: int    = Field(default=200, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


# ── Output ─────────────────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    id: str
    model: str
    created: int
    choices: list[dict]
    usage: dict
