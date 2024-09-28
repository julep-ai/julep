from langchain_community.document_loaders import WikipediaLoader

from ...models import WikipediaArguments, WikipediaOutput


async def wikipedia(arguments: WikipediaArguments) -> WikipediaOutput:
    """
    Searches Wikipedia for a given query and returns formatted results.
    """

    query = arguments.query
    if not query:
        raise ValueError("Query parameter is required for Wikipedia search")

    load_max_docs = arguments.load_max_docs

    loader = WikipediaLoader(query=query, load_max_docs=load_max_docs)
    documents = loader.load()

    return WikipediaOutput(documents=documents)
