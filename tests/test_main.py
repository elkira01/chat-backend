import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from src.config import OLLAMA_BASE_URL
from src.main import app

client = TestClient(app)


@respx.mock
def test_health_check_success():
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    respx.get(url).mock(
        return_value=httpx.Response(200, json={"models": [{"name": "llama3"}]})
    )

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ollama_reachable"] == True
    assert response.json()["models"] == ["llama3"]


@respx.mock
def test_health_check_failure():
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    respx.get(url).mock(side_effect=httpx.ConnectError("Network error"))

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ollama_reachable"] == False


def test_chat_endpoint_plain(mocker):
    mocker.patch("src.main.should_search_web", return_value=False)
    mocker.patch("src.main.generate_response", return_value="Hello there")

    response = client.post(
        "/chat", json={"message": "hi", "model": "llama", "history": []}
    )
    assert response.status_code == 200
    assert response.json() == {
        "reply": "Hello there",
        "sources": [],
        "used_search": False,
    }


def test_chat_endpoint_search(mocker):
    mocker.patch("src.main.should_search_web", return_value=True)
    mocker.patch("src.main.generate_response", return_value="Here is info from search")

    from src.web.factory import SearchResult

    mock_search = mocker.AsyncMock()
    mock_search.return_value = [
        SearchResult(title="Test", url="http://example.com", snippet="Snippet", score=1)
    ]
    mock_provider = mocker.MagicMock()
    mock_provider.search = mock_search
    mocker.patch("src.main.WebSearchProviderFactory.create", return_value=mock_provider)

    response = client.post(
        "/chat", json={"message": "news", "model": "llama", "history": []}
    )
    assert response.status_code == 200
    assert response.json()["used_search"] == True
    assert response.json()["sources"] == ["http://example.com"]
    assert response.json()["reply"] == "Here is info from search"


def test_chat_endpoint_search_fallback(mocker):
    mocker.patch("src.main.should_search_web", return_value=True)
    mocker.patch("src.main.generate_response", return_value="Fallback reply")

    mock_provider = mocker.MagicMock()
    mock_provider.search = mocker.AsyncMock(side_effect=Exception("Search Error"))
    mocker.patch("src.main.WebSearchProviderFactory.create", return_value=mock_provider)

    response = client.post(
        "/chat", json={"message": "news", "model": "llama", "history": []}
    )
    assert response.status_code == 200
    assert response.json()["used_search"] == False
    assert response.json()["sources"] == []
    assert response.json()["reply"] == "Fallback reply"


def test_chat_endpoint_generation_exception(mocker):
    mocker.patch("src.main.should_search_web", return_value=False)
    mocker.patch(
        "src.main.generate_response", side_effect=Exception("Generation failed")
    )

    response = client.post(
        "/chat", json={"message": "hi", "model": "llama", "history": []}
    )
    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to generate response"}


def test_chat_stream_endpoint(mocker):
    mocker.patch("src.main.should_search_web", return_value=False)

    async def mock_stream_response(messages, model):
        yield "Hello"
        yield " World"

    mocker.patch("src.main.stream_response", side_effect=mock_stream_response)

    response = client.post(
        "/chat/stream", json={"message": "hi", "model": "llama", "history": []}
    )
    assert response.status_code == 200

    content = response.text
    assert 'data: {"meta": {"used_search": false, "sources": []}}' in content
    assert 'data: {"chunk": "Hello"}' in content
    assert 'data: {"chunk": " World"}' in content
    assert "data: [DONE]" in content


def test_chat_stream_endpoint_exception(mocker):
    mocker.patch("src.main.should_search_web", return_value=False)

    async def mock_stream_response_error(messages, model):
        yield "Hello"
        raise Exception("Stream error")

    mocker.patch("src.main.stream_response", side_effect=mock_stream_response_error)

    response = client.post(
        "/chat/stream", json={"message": "hi", "model": "llama", "history": []}
    )
    assert response.status_code == 200

    content = response.text
    assert 'data: {"meta": {"used_search": false, "sources": []}}' in content
    assert 'data: {"chunk": "Hello"}' in content
    assert 'data: {"error": "Stream error"}' in content
    assert "data: [DONE]" in content
