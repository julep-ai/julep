from langchain_community.document_loaders import HNLoader


async def hacker_news(arguments: dict) -> str:
    """
    Fetches and formats content from a Hacker News thread using the provided URL.
    """
    url = arguments.get("url")
    if not url:
        raise ValueError("URL parameter is required for Hacker News search")
    loader = HNLoader(url)
    documents = loader.load()

    if not documents:
        raise ValueError("No data found for the given URL")

    # data is a list of documents,
    result = "\n\n".join(
        [
            f"Title: {doc.metadata['title']}\n"
            f"Source: {doc.metadata['source']}\n"
            f"Content: {doc.page_content}..."
            for doc in documents
        ]
    )
    return result
