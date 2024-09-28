from langchain_community.document_loaders import SpiderLoader

from ...models import SpiderArguments, SpiderOutput, SpiderSetup


async def spider(setup: SpiderSetup, arguments: SpiderArguments) -> SpiderOutput:
    """
    Fetches data from a specified URL.
    """

    assert isinstance(setup, SpiderSetup), "Invalid setup"
    assert isinstance(arguments, SpiderArguments), "Invalid arguments"

    query = arguments.query

    if not query:
        raise ValueError("URL parameter is required for spider")

    spider_loader = SpiderLoader(
        api_key=setup.spider_api_key,
        base_url=arguments.query,
        mode=arguments.mode,
        params=arguments.params,
    )

    documents = spider_loader.load()

    return SpiderOutput(result=documents)
