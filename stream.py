"""
Streaming SSE handler.
Converts DOM text chunks from the automator into OpenAI-compatible
Server-Sent Events (SSE) format for streaming responses.
"""

import json
import uuid
import time
from typing import AsyncGenerator

from models import ChatCompletionChunk, StreamChoice, DeltaContent


def _make_chunk_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex[:12]}"


async def chunks_to_sse(
    text_chunks: AsyncGenerator[str, None],
    model: str,
) -> AsyncGenerator[str, None]:
    """
    Convert an async generator of text deltas into OpenAI SSE format.

    Yields strings like:
        data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk",...}\n\n
    Ends with:
        data: [DONE]\n\n
    """
    chunk_id = _make_chunk_id()
    created = int(time.time())

    # First chunk: send role
    first_chunk = ChatCompletionChunk(
        id=chunk_id,
        created=created,
        model=model,
        choices=[
            StreamChoice(
                delta=DeltaContent(role="assistant", content=""),
                finish_reason=None,
            )
        ],
    )
    yield f"data: {first_chunk.model_dump_json()}\n\n"

    # Content chunks
    async for text_delta in text_chunks:
        if not text_delta:
            continue
        chunk = ChatCompletionChunk(
            id=chunk_id,
            created=created,
            model=model,
            choices=[
                StreamChoice(
                    delta=DeltaContent(content=text_delta),
                    finish_reason=None,
                )
            ],
        )
        yield f"data: {chunk.model_dump_json()}\n\n"

    # Final chunk: send finish_reason
    final_chunk = ChatCompletionChunk(
        id=chunk_id,
        created=created,
        model=model,
        choices=[
            StreamChoice(
                delta=DeltaContent(),
                finish_reason="stop",
            )
        ],
    )
    yield f"data: {final_chunk.model_dump_json()}\n\n"

    # Done sentinel
    yield "data: [DONE]\n\n"
