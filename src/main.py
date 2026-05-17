from fastapi import FastAPI, Query
from pydantic import BaseModel

from config import MAX_SEARCH_RESULTS, WEB_SEARCH_API_KEY, WEB_SEARCH_PROVIDER
from web.factory import SearchResult, WebSearchProviderFactory

app = FastAPI()


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]

    model_config = {"arbitrary_types_allowed": True}


@app.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query"),
    max_results: int = Query(default=None, description="Max results to return"),
):
    if max_results is None:
        max_results = int(MAX_SEARCH_RESULTS)

    provider = WebSearchProviderFactory.create(WEB_SEARCH_PROVIDER, WEB_SEARCH_API_KEY)
    results = await provider.search(q, max_results)
    return SearchResponse(query=q, results=results)