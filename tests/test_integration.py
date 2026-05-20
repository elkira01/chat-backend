import os

import httpx
import pytest
from fastapi.testclient import TestClient

from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL, WEB_SEARCH_API_KEY
from src.main import app

client = TestClient(app)


# Helper function to check if Ollama is actually running locally
def get_ollama_status():
    try:
        response = httpx.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=2.0)
        if response.status_code == 200:
            models = [m.get("name") for m in response.json().get("models", [])]
            # Strip tags for basic matching, or exact match if you want
            model_exists = any(OLLAMA_MODEL in m for m in models)
            return True, model_exists
        return False, False
    except Exception:
        return False, False


IS_OLLAMA_RUNNING, HAS_MODEL = get_ollama_status()


# Apply the 'integration' marker to all tests in this file
pytestmark = pytest.mark.integration


@pytest.mark.skipif(not IS_OLLAMA_RUNNING, reason="Ollama is not currently running.")
def test_integration_health_check():
    """Test the /health endpoint against a real Ollama instance."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["ollama_reachable"] is True
    assert isinstance(data["models"], list)


@pytest.mark.skipif(
    not IS_OLLAMA_RUNNING or not HAS_MODEL,
    reason=f"Ollama is not running, or model '{OLLAMA_MODEL}' is missing.",
)
def test_integration_chat_plain():
    """
    Test the full /chat flow without web search.
    This uses the real router to decide NOT to search, and the real LLM to generate text.
    """
    payload = {
        "message": "Say exactly the word 'PINEAPPLE' and nothing else.",
        "history": [],
    }
    response = client.post("/chat", json=payload, timeout=30.0)
    assert response.status_code == 200

    data = response.json()
    assert data["used_search"] is False
    assert len(data["sources"]) == 0
    # The LLM should respond with PINEAPPLE
    assert "PINEAPPLE" in data["reply"].upper()


@pytest.mark.skipif(
    not IS_OLLAMA_RUNNING or not HAS_MODEL or WEB_SEARCH_API_KEY in ("dummy", "", None),
    reason=f"Missing dependencies: Ollama running={IS_OLLAMA_RUNNING}, Model={HAS_MODEL}, API_KEY present",
)
def test_integration_chat_search():
    """
    Test the full /chat flow WITH web search.
    This requires both Ollama and a real Search API key.
    """
    payload = {"message": "What is the latest news today?", "history": []}
    response = client.post("/chat", json=payload, timeout=30.0)
    # assert response.status_code == 200

    data = response.json()
    assert data["used_search"] is True
    # If search was triggered and succeeded, we should have sources
    assert len(data["sources"]) > 0
    assert len(data["reply"]) > 0


@pytest.mark.skipif(
    not IS_OLLAMA_RUNNING or not HAS_MODEL,
    reason=f"Ollama is not running, or model '{OLLAMA_MODEL}' is missing.",
)
def test_integration_chat_stream():
    """Test the streaming endpoint end-to-end."""
    payload = {"message": "Write a 5 word sentence.", "history": []}
    with client.stream("POST", "/chat/stream", json=payload) as response:
        assert response.status_code == 200

        chunks = list(response.iter_lines())
        # Filter out empty lines caused by \n\n
        chunks = [c for c in chunks if c.strip()]

        assert len(chunks) > 0

        # The first meaningful line should be the meta data
        meta_line = next(line for line in chunks if line.startswith('data: {"meta"'))
        assert "used_search" in meta_line

        # The stream should end with [DONE]
        assert chunks[-1] == "data: [DONE]"
