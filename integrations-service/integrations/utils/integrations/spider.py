from langchain_community.document_loaders import SpiderLoader
from tenacity import retry, stop_after_attempt, wait_exponential

from ...models import SpiderFetchArguments, SpiderFetchOutput, SpiderSetup


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def crawl(
    setup: SpiderSetup, arguments: SpiderFetchArguments
) -> SpiderFetchOutput:
    """
    Fetches data from a specified URL.
    """

    assert isinstance(setup, SpiderSetup), "Invalid setup"
    assert isinstance(arguments, SpiderFetchArguments), "Invalid arguments"

    url = arguments.url

    if not url:
        raise ValueError("URL parameter is required for spider")

    spider_loader = SpiderLoader(
        api_key=setup.spider_api_key,
        url=str(url),
        mode=arguments.mode,
        params=arguments.params,
    )

    documents = spider_loader.load()

    return SpiderFetchOutput(documents=documents)
