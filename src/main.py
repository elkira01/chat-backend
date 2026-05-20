import json
import logging
import sys
from pathlib import Path
from typing import AsyncGenerator

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.config import (
    ALLOWED_ORIGINS,
    MAX_SEARCH_RESULTS,
    OLLAMA_BASE_URL,
    WEB_SEARCH_API_KEY,
    WEB_SEARCH_PROVIDER,
)
from src.llm import generate_response, stream_response
from src.prompt import build_augmented_messages, build_plain_messages
from src.router import should_search_web
from src.web.factory import SearchResult, WebSearchProviderFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if ALLOWED_ORIGINS:
    origins = [origin.strip() for origin in ALLOWED_ORIGINS.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []


class ChatResponse(BaseModel):
    reply: str
    sources: list[str] = []
    used_search: bool


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [m.get("name") for m in data.get("models", [])]
            return {"status": "ok", "ollama_reachable": True, "models": models}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "ollama_reachable": False, "details": str(e)}


async def _process_chat_request(
    request: ChatRequest,
) -> tuple[list[dict], list[str], bool]:
    history_dicts = [
        {"role": msg.role, "content": msg.content} for msg in request.history
    ]

    use_search = await should_search_web(request.message)
    sources = []
    messages = []

    if use_search:
        logger.info("Web search triggered")
        try:
            provider = WebSearchProviderFactory.create(
                WEB_SEARCH_PROVIDER, WEB_SEARCH_API_KEY
            )
            results = await provider.search(request.message, int(MAX_SEARCH_RESULTS))
            sources = [res.url for res in results]
            messages = build_augmented_messages(request.message, history_dicts, results)
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            # Fallback to plain prompt on search failure
            use_search = False
            messages = build_plain_messages(request.message, history_dicts)
    else:
        messages = build_plain_messages(request.message, history_dicts)

    return messages, sources, use_search


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(request: Request, chat_request: ChatRequest):
    messages, sources, use_search = await _process_chat_request(chat_request)

    # for msg in messages:
    # logger.info(f"\n\nMessage: {msg}\n\n")

    try:
        reply = await generate_response(messages)
        return ChatResponse(reply=reply, sources=sources, used_search=use_search)
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response")


@app.post("/chat/stream")
@limiter.limit("20/minute")
async def chat_stream(request: Request, chat_request: ChatRequest):
    messages, sources, use_search = await _process_chat_request(chat_request)

    async def sse_generator() -> AsyncGenerator[str, None]:
        # First yield the metadata
        meta = {"used_search": use_search, "sources": sources}
        yield f"data: {json.dumps({'meta': meta})}\n\n"

        try:
            async for chunk in stream_response(messages):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            logger.error(f"LLM streaming failed: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=False)
