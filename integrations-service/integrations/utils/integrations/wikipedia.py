from langchain_community.document_loaders import WikipediaLoader

from ...models import WikipediaExecutionArguments


async def wikipedia(arguments: WikipediaExecutionArguments) -> str:
    """
    Searches Wikipedia for a given query and returns formatted results.
    """

    query = arguments.query
    if not query:
        raise ValueError("Query parameter is required for Wikipedia search")

    load_max_docs = arguments.load_max_docs

    loader = WikipediaLoader(query=query, load_max_docs=load_max_docs)
    documents = loader.load()

    # Format the results as string
    result = "\n\n".join(
        [
            f"Title: {doc.metadata['title']}\n"
            f"Summary: {doc.metadata['summary']}\n"
            f"Content: {doc.page_content}..."
            for doc in documents
        ]
    )
    return result
