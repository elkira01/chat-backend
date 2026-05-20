import httpx
import pytest
import respx

from src.web.factory import WebSearchProviderFactory
from src.web.provider import BraveProvider, SerpAPIProvider, TavilyProvider


def test_factory_creates_providers():
    tavily = WebSearchProviderFactory.create("tavily", "key1")
    assert isinstance(tavily, TavilyProvider)
    assert tavily.api_key == "key1"

    with pytest.raises(ValueError, match="Unknown search provider"):
        WebSearchProviderFactory.create("unknown", "key")


@pytest.mark.asyncio
@respx.mock
async def test_tavily_provider():
    provider = TavilyProvider("key")
    respx.post(TavilyProvider.BASE_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [{"title": "T1", "url": "U1", "content": "S1", "score": 1}]
            },
        )
    )
    results = await provider.search("query")
    assert len(results) == 1
    assert results[0].title == "T1"
    assert results[0].snippet == "S1"


@pytest.mark.asyncio
@respx.mock
async def test_brave_provider():
    provider = BraveProvider("key")
    respx.get(BraveProvider.BASE_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "web": {
                    "results": [
                        {"title": "T1", "url": "U1", "description": "S1", "score": 1}
                    ]
                }
            },
        )
    )
    results = await provider.search("query")
    assert len(results) == 1
    assert results[0].title == "T1"
    assert results[0].snippet == "S1"


@pytest.mark.asyncio
@respx.mock
async def test_serpapi_provider():
    provider = SerpAPIProvider("key")
    respx.get(SerpAPIProvider.BASE_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "organic_results": [
                    {"title": "T1", "link": "U1", "snippet": "S1", "score": 1}
                ]
            },
        )
    )
    results = await provider.search("query")
    assert len(results) == 1
    assert results[0].url == "U1"
    assert results[0].snippet == "S1"
