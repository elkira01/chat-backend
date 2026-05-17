from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    score: int


class WebSearchProvider(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        ...

class WebSearchProviderFactory:
    @classmethod
    def create(cls, provider_name: str, api_key: str) -> WebSearchProvider:
        from web.provider import BraveProvider, SerpAPIProvider, TavilyProvider

        _providers: dict[str, type[WebSearchProvider]] = {
            "tavily": TavilyProvider,
            "brave": BraveProvider,
            "serpapi": SerpAPIProvider,
        }

        provider_name = provider_name.lower()
        provider_cls = _providers.get(provider_name)
        if provider_cls is None:
            raise ValueError(
                f"Unknown search provider '{provider_name}'. "
                f"Available providers: {', '.join(_providers)}"
            )
        return provider_cls(api_key)