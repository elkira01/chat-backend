import json
from typing import AsyncGenerator

import httpx

from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL


async def generate_response(messages: list[dict], model: str = None) -> str:
    """Standard non-streaming request to Ollama."""
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/v1/chat/completions"
    payload = {"model": model or OLLAMA_MODEL, "messages": messages, "stream": False}

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def stream_response(
    messages: list[dict], model: str = None
) -> AsyncGenerator[str, None]:
    """Streaming request to Ollama."""
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/v1/chat/completions"
    payload = {"model": model or OLLAMA_MODEL, "messages": messages, "stream": True}

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue
