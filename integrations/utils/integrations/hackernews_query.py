from langchain_community.document_loaders import HNLoader

async def hackernews_query(parameters: dict) -> str:
    url = parameters.get("url")
    if not url:
        raise ValueError(
            "URL parameter is required for Hacker News search"
        )
    loader = HNLoader(url)
    documents = loader.load()

    if not documents:
        raise ValueError("No data found for the given URL")

    # data is a list of documents,
    result = "\n\n".join([
        f"Title: {doc.metadata['title']}\n"
        f"Source: {doc.metadata['source']}\n"
        f"Content: {doc.page_content}..."
        for doc in documents
    ])
    return result
