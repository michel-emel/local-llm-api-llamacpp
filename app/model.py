"""
model.py — LLM singleton + async wrapper

The llama_cpp inference call is CPU-blocking. Running it directly
inside an async FastAPI route would freeze the entire server for
every other request during generation.

Solution: run_in_executor() pushes the blocking call to a thread pool,
freeing the event loop to handle other requests in parallel.
"""

import asyncio
import logging
from functools import partial
from pathlib import Path

from llama_cpp import Llama

logger = logging.getLogger(__name__)

MODEL_PATH = Path("models/phi2/phi-2.Q4_K_M.gguf")

# ── Load once at startup ───────────────────────────────────────────────────────
def _load_model() -> Llama:
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model not found: {MODEL_PATH}")
    logger.info("Loading model %s …", MODEL_PATH.name)
    model = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=4096,       # large enough for RAG (docs eat tokens)
        n_threads=8,
        n_batch=256,      # CPU throughput improvement
        n_gpu_layers=0,   # set >0 if you have a GPU
        verbose=False,
    )
    logger.info("Model loaded ✓")
    return model

llm: Llama = _load_model()

# ── Async wrappers ─────────────────────────────────────────────────────────────

async def generate_async(prompt: str, **kwargs) -> dict:
    """Non-blocking single completion."""
    loop = asyncio.get_event_loop()
    fn = partial(llm, prompt, **kwargs)
    return await loop.run_in_executor(None, fn)


async def stream_async(prompt: str, **kwargs):
    """
    Async generator that yields raw llama_cpp chunks.
    Streaming is inherently token-by-token so we run each
    next() call in the executor to avoid blocking.
    """
    loop = asyncio.get_event_loop()

    # Build the sync generator in the executor
    fn = partial(llm, prompt, stream=True, **kwargs)
    gen = await loop.run_in_executor(None, fn)

    while True:
        try:
            chunk = await loop.run_in_executor(None, next, gen)
            yield chunk
        except StopIteration:
            break
