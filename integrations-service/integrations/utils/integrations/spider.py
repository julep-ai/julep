from ...models import SpiderExecutionArguments, SpiderExecutionSetup
from langchain_community.document_loaders import SpiderLoader

async def spider(
    setup: SpiderExecutionSetup, arguments: SpiderExecutionArguments) -> str:
    """
    Fetches data from a specified URL.
    """

    assert isinstance(setup, SpiderExecutionSetup), "Invalid setup"
    assert isinstance(arguments, SpiderExecutionArguments), "Invalid arguments"

    query = arguments.query

    if not query:
        raise ValueError("URL parameter is required for spider")
    
    spider_loader = SpiderLoader(
        api_key=setup.spider_api_key,
        base_url=arguments.query,
        mode=arguments.mode,
        params=arguments.params
    )

    documents = spider_loader.load()

    # Format the results as string
    result = "\n\n".join(
        [
            f"Title: {doc.metadata['title']}\n"
            f"Content: {doc.page_content}..."
            for doc in documents
        ]
    )

    return result




