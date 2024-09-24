from langchain_community.tools import DuckDuckGoSearchRun


async def duckduckgo_search(parameters: dict) -> str:
    """
    Performs a web search using DuckDuckGo and returns the results.
    """
    search = DuckDuckGoSearchRun()
    query = parameters.get("query")
    if not query:
        raise ValueError("Query parameter is required for DuckDuckGo search")
    return search.run(query)
