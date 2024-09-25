from langchain_community.tools import DuckDuckGoSearchRun

from ...models import DuckDuckGoSearchExecutionArguments


async def duckduckgo_search(arguments: DuckDuckGoSearchExecutionArguments) -> str:
    """
    Performs a web search using DuckDuckGo and returns the results.
    """

    search = DuckDuckGoSearchRun()
    query = arguments.query
    if not query:
        raise ValueError("Query parameter is required for DuckDuckGo search")
    return search.run(query)
