import httpx

from web.factory import SearchResult, WebSearchProvider

class TavilyProvider(WebSearchProvider):
    BASE_URL = "https://api.tavily.com/search"

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL,
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                },
            )
            response.raise_for_status()
            data = response.json()
            return [
                SearchResult(
                    title=r["title"],
                    url=r["url"],
                    snippet=r.get("content", ""),
                    score=r.get("score", 0),
                )
                for r in data.get("results", [])
            ]


class BraveProvider(WebSearchProvider):
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.BASE_URL,
                params={"q": query, "count": max_results},
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.api_key,
                },
            )
            response.raise_for_status()
            data = response.json()
            return [
                SearchResult(
                    title=r["title"],
                    url=r["url"],
                    snippet=r.get("description", ""),
                    score=r.get("score", 0),
                )
                for r in data.get("web", {}).get("results", [])
            ]


class SerpAPIProvider(WebSearchProvider):
    BASE_URL = "https://serpapi.com/search"

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.BASE_URL,
                params={
                    "api_key": self.api_key,
                    "q": query,
                    "num": max_results,
                    "engine": "google",
                },
            )
            response.raise_for_status()
            data = response.json()
            return [
                SearchResult(
                    title=r["title"],
                    url=r["link"],
                    snippet=r.get("snippet", ""),
                    score=r.get("score", 0),
                )
                for r in data.get("organic_results", [])
            ]


