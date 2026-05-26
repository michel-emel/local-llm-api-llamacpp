"""
main.py — FastAPI application

Endpoints:
  GET  /health          liveness check
  GET  /model-info      model metadata (debug)
  POST /chat            multi-turn chat (+ RAG context + session memory)
  POST /generate        single-turn backward-compat
  DELETE /session/{id}  clear a session's memory
"""

import json
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app.model import generate_async, stream_async, llm, MODEL_PATH
from app.prompt import build_prompt, STOP_TOKENS
from app.schemas import ChatRequest, ChatResponse, GenerateRequest
from app import memory

# ── App setup ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Local LLM API", version="3.0")


# ── SSE stream helper ──────────────────────────────────────────────────────────

async def sse_stream(prompt: str, max_tokens: int, temperature: float, top_p: float):
    """Yield Server-Sent Events from the async token stream."""
    request_id = str(uuid.uuid4())
    created = int(time.time())

    yield "retry: 1000\n\n"   # tell the client to reconnect after 1 s on drop

    async for chunk in stream_async(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        stop=STOP_TOKENS,
    ):
        token = chunk["choices"][0]["text"]
        payload = {
            "id": request_id,
            "created": created,
            "choices": [{"delta": {"content": token}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(payload)}\n\n"

    yield f"data: {json.dumps({'choices': [{'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
    yield "data: [DONE]\n\n"


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_PATH.name}


@app.get("/model-info")
async def model_info():
    """Return raw model metadata — handy for debugging context size etc."""
    return llm.metadata


@app.post("/chat", response_model=None)
async def chat(req: ChatRequest):
    """
    Multi-turn chat with optional RAG context and session memory.

    Flow:
        1. Load session history (if session_id given)
        2. Merge history + new messages
        3. Build prompt (inject RAG context if present)
        4. Generate (stream or not)
        5. Save new turns to session memory
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")

    # 1. Merge session history with incoming messages
    history = memory.get(req.session_id) if req.session_id else []

    # Avoid duplicating turns already in history
    # Convention: client always sends the FULL new message(s), history holds past turns
    merged = history + req.messages

    # 2. Build prompt
    prompt = build_prompt(merged, context=req.context)
    logger.info(
        "Chat | session=%s | turns=%d | rag=%s | stream=%s",
        req.session_id, len(merged), bool(req.context), req.stream,
    )

    # 3. Stream response
    if req.stream:
        return StreamingResponse(
            sse_stream(prompt, req.max_tokens, req.temperature, req.top_p),
            media_type="text/event-stream",
        )

    # 4. Blocking generation (async-safe via executor)
    result = await generate_async(
        prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
        stop=STOP_TOKENS,
    )

    answer = result["choices"][0]["text"].strip()
    usage  = result.get("usage", {})

    # 5. Persist turns to session memory
    if req.session_id:
        # Save the last user message and the reply
        last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
        if last_user:
            memory.add(req.session_id, "user", last_user.content)
        memory.add(req.session_id, "assistant", answer)

    return ChatResponse(
        id=str(uuid.uuid4()),
        model=MODEL_PATH.name,
        created=int(time.time()),
        choices=[{"message": {"role": "assistant", "content": answer}}],
        usage=usage,
    )


@app.post("/generate")
async def generate(req: GenerateRequest):
    """Backward-compatible single-turn endpoint."""
    result = await generate_async(
        req.prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        stop=STOP_TOKENS,
    )
    return {"response": result["choices"][0]["text"].strip()}


@app.delete("/session/{session_id}")
async def reset_session(session_id: str):
    """Clear a session's conversation history."""
    memory.clear(session_id)
    return {"cleared": session_id}
