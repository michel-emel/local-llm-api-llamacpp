"""
prompt.py — Prompt builder

Keeps prompt formatting in one place.
When you switch models (Mistral, LLaMA-3, Gemma…) you only
change this file — nothing else in the API changes.

Phi-2 works best with plain User/Assistant format (NOT Instruction/Response).
"""

from typing import Optional
from app.schemas import Message


STOP_TOKENS = ["</s>", "User:", "System:"]


def build_prompt(messages: list[Message], context: Optional[str] = None) -> str:
    """
    Build the final prompt string sent to the model.

    Layout:
        [System message if present]

        Context:           ← RAG block, injected ONCE at the top
        <retrieved docs>

        User: …
        Assistant: …
        User: …
        Assistant:         ← model continues from here
    """
    prompt = ""

    # 1. System message (personality / instructions)
    system_msgs = [m for m in messages if m.role.lower() == "system"]
    if system_msgs:
        prompt += system_msgs[-1].content.strip() + "\n\n"

    # 2. RAG context block — always at the top, before conversation turns.
    #    Your retriever passes the chunks here; the model sees them before
    #    the conversation so it can cite them when answering.
    if context:
        prompt += f"Context:\n{context.strip()}\n\n"

    # 3. Conversation turns (skip system messages, already handled)
    for m in messages:
        role = m.role.lower()
        if role == "user":
            prompt += f"User: {m.content.strip()}\n"
        elif role == "assistant":
            prompt += f"Assistant: {m.content.strip()}\n"

    # 4. Prime the model to generate the next assistant turn
    prompt += "Assistant: "
    return prompt
