"""
FastAPI server exposing OpenAI-compatible endpoints.
All chat completions are fulfilled by automating claude.ai via Playwright.
Zero credentials — no API keys, no auth tokens, no .env files.
"""

import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from automator import Automator
from browser import BrowserManager
from models import (
    AVAILABLE_MODELS,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Choice,
    ModelList,
    Usage,
)
from stream import chunks_to_sse

log = logging.getLogger("cww.server")

app = FastAPI(
    title="Claude Web Wrapper",
    description="OpenAI-compatible API bridge for claude.ai via DOM automation",
    version="0.1.0",
)

# CORS — required for OpenClaw/Open WebUI to call us from a different port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state — set by main.py before server starts
_browser: BrowserManager | None = None
_automator: Automator | None = None
_lock = asyncio.Lock()


def set_browser(browser: BrowserManager):
    global _browser, _automator
    _browser = browser
    _automator = Automator(browser.page)


def _format_messages(messages: list[ChatMessage]) -> str:
    """
    Concatenate chat messages into a single prompt string.
    Claude.ai's input is a single text box, so we format multi-turn
    conversations into a readable prompt.
    """
    if len(messages) == 1:
        return messages[0].content

    parts = []
    for msg in messages:
        if msg.role == "system":
            parts.append(f"[System]\n{msg.content}")
        elif msg.role == "user":
            parts.append(f"[User]\n{msg.content}")
        elif msg.role == "assistant":
            parts.append(f"[Assistant]\n{msg.content}")
        else:
            parts.append(msg.content)
    return "\n\n".join(parts)


# =============================================================================
# Endpoints
# =============================================================================


@app.get("/v1/models")
async def list_models() -> ModelList:
    """Return available Claude models."""
    log.info("[API] GET /v1/models")
    return AVAILABLE_MODELS


@app.get("/health")
async def health_check():
    """Check if the browser is alive and on claude.ai."""
    if not _browser:
        raise HTTPException(status_code=503, detail="Browser not initialized")

    logged_in = await _browser.is_logged_in()
    return {
        "status": "ok" if logged_in else "not_logged_in",
        "logged_in": logged_in,
        "message": (
            "Ready" if logged_in
            else "Not logged in — restart with --headed to log in"
        ),
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.
    Automates claude.ai DOM to send messages and stream responses.
    """
    if not _automator:
        raise HTTPException(status_code=503, detail="Browser not initialized")

    log.info(
        "[API] POST /v1/chat/completions — model=%s stream=%s messages=%d",
        request.model,
        request.stream,
        len(request.messages),
    )

    # Serialize requests (one chat at a time — claude.ai is single-threaded)
    async with _lock:
        try:
            return await _handle_completion(request)
        except Exception as e:
            log.error("[ERROR] Chat completion failed: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))


async def _handle_completion(request: ChatCompletionRequest):
    """Core logic for handling a chat completion request."""
    # Check usage limit
    if await _automator.check_usage_limit():
        raise HTTPException(
            status_code=429,
            detail="Claude.ai weekly usage limit reached",
        )

    # Start a fresh chat
    await _automator.start_new_chat()

    # Select model if specified
    await _automator.select_model(request.model)

    # Format and send the message
    prompt = _format_messages(request.messages)
    await _automator.send_message(prompt)

    if request.stream:
        # Streaming response
        return StreamingResponse(
            chunks_to_sse(_automator.stream_response(), model=request.model),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # Non-streaming: wait for full response
        full_text = await _automator.get_full_response()

        return ChatCompletionResponse(
            model=request.model,
            choices=[
                Choice(
                    message=ChatMessage(role="assistant", content=full_text),
                    finish_reason="stop",
                )
            ],
            usage=Usage(
                prompt_tokens=len(prompt.split()),
                completion_tokens=len(full_text.split()),
                total_tokens=len(prompt.split()) + len(full_text.split()),
            ),
        )
