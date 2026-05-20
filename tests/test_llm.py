import httpx
import pytest
import respx

from src.config import OLLAMA_BASE_URL
from src.llm import generate_response, stream_response


@pytest.mark.asyncio
@respx.mock
async def test_generate_response():
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/v1/chat/completions"
    mock_resp = {"choices": [{"message": {"content": "Hello World"}}]}
    respx.post(url).mock(return_value=httpx.Response(200, json=mock_resp))

    messages = [{"role": "user", "content": "hi"}]
    reply = await generate_response(messages, "llama3.2:1b")
    assert reply == "Hello World"


@pytest.mark.asyncio
@respx.mock
async def test_stream_response():
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/v1/chat/completions"

    # Simulate SSE stream with a normal chunk and a malformed chunk to test the JSONDecodeError try-except
    content = (
        'data: {"choices": [{"delta": {"content": "Hello"}}]}\n\n'
        'data: {"choices": [{"delta": {"content": " World"}}]}\n\n'
        "data: {malformed_json_here}\n\n"
        "data: [DONE]\n\n"
    )
    respx.post(url).mock(return_value=httpx.Response(200, content=content))

    messages = [{"role": "user", "content": "hi"}]
    chunks = []
    async for chunk in stream_response(messages, "llama3.2:1b"):
        chunks.append(chunk)

    assert "".join(chunks) == "Hello World"
