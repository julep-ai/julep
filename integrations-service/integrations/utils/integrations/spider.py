import asyncio
from functools import lru_cache
from typing import Any, Dict

from beartype import beartype
from langchain_community.document_loaders import SpiderLoader
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import SpiderFetchArguments, SpiderSetup
from ...env import spider_api_key  # Import env to access environment variables
from ...models import SpiderFetchOutput


# Cache spider client instances
@lru_cache(maxsize=100)
def get_spider_client(api_key: str, **kwargs) -> SpiderLoader:
    return SpiderLoader(api_key=api_key, **kwargs)


@beartype
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

    api_key = (
        setup.spider_api_key
        if setup.spider_api_key != "DEMO_API_KEY"
        else spider_api_key
    )

    spider_loader = get_spider_client(
        api_key=api_key,
        url=str(arguments.url),
        mode=arguments.mode,
        params=arguments.params,
    )

    documents = await asyncio.to_thread(spider_loader.load)
    return SpiderFetchOutput(documents=documents)
