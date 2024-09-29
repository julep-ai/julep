from langchain_community.document_loaders import HNLoader

from ...models import HackerNewsFetchArguments, HackerNewsFetchOutput


async def fetch(arguments: HackerNewsFetchArguments) -> HackerNewsFetchOutput:
    """
    Fetches and formats content from a Hacker News thread using the provided URL.
    """

    assert isinstance(arguments, HackerNewsFetchArguments), "Invalid arguments"

    url = arguments.url
    if not url:
        raise ValueError("URL parameter is required for Hacker News search")
    loader = HNLoader(str(url))
    documents = loader.load()

    if not documents:
        raise ValueError("No data found for the given URL")

    return HackerNewsFetchOutput(documents=documents)
