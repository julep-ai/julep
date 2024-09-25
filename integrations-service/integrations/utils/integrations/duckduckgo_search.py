from langchain_community.tools import DuckDuckGoSearchRun

from ...models import DuckDuckGoSearchExecutionParams


async def duckduckgo_search(parameters: DuckDuckGoSearchExecutionParams) -> str:
    """
    Performs a web search using DuckDuckGo and returns the results.
    """
    search = DuckDuckGoSearchRun()
    query = parameters.query
    if not query:
        raise ValueError("Query parameter is required for DuckDuckGo search")
    return search.run(query)
