from beartype import beartype
from spider import AsyncSpider
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import SpiderFetchArguments, SpiderSetup
from ...env import (
    spider_api_key,  # Import env to access environment variables
)
from ...models import SpiderOutput, SpiderResponse


# Spider client instances
def get_spider_client(api_key: str) -> AsyncSpider:
    return AsyncSpider(api_key=api_key)


def get_api_key(setup: SpiderSetup) -> str:
    """
    Helper function to get the API key.
    """
    return (
        setup.spider_api_key
        if setup.spider_api_key != "DEMO_API_KEY"
        else spider_api_key
    )


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def crawl(setup: SpiderSetup, arguments: SpiderFetchArguments) -> SpiderOutput:
    """
    Crawl a website and extract data.
    """
    assert isinstance(setup, SpiderSetup), "Invalid setup"
    assert isinstance(arguments, SpiderFetchArguments), "Invalid arguments"

    api_key = get_api_key(setup)

    # Initialize final_result
    final_result = []
    results = None

    # Initialize spider_client
    async with get_spider_client(api_key=api_key) as spider_client:
        async for result in spider_client.crawl_url(
            url=str(arguments.url),
            params=arguments.params,
            stream=False,
            content_type=arguments.content_type,
        ):
            results = result

        for page in results:
            final_result.append(
                SpiderResponse(
                    url=page["url"] if page["url"] is not None else None,
                    content=page["content"] if page["content"] is not None else None,
                    error=page["error"] if page["error"] is not None else None,
                    status=page["status"] if page["status"] is not None else None,
                    costs=page["costs"] if page["costs"] is not None else None,
                )
            )
    # Return final_result
    return SpiderOutput(result=final_result)


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def links(setup: SpiderSetup, arguments: SpiderFetchArguments) -> SpiderOutput:
    """
    Extract all links from the webpage.
    """
    assert isinstance(setup, SpiderSetup), "Invalid setup"
    assert isinstance(arguments, SpiderFetchArguments), "Invalid arguments"

    api_key = get_api_key(setup)

    # Initialize final_result
    final_result = []
    results = None

    # Initialize spider_client
    async with get_spider_client(api_key=api_key) as spider_client:
        async for result in spider_client.links(
            url=str(arguments.url),
            params=arguments.params,
            stream=False,
            content_type=arguments.content_type,
        ):
            results = result

        for page in results:
            final_result.append(
                SpiderResponse(
                    url=page["url"] if page["url"] is not None else None,
                    content=page["content"] if page["content"] is not None else None,
                    error=page["error"] if page["error"] is not None else None,
                    status=page["status"] if page["status"] is not None else None,
                    costs=page["costs"] if page["costs"] is not None else None,
                )
            )
    # Return final_result
    return SpiderOutput(result=final_result)


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def screenshot(
    setup: SpiderSetup, arguments: SpiderFetchArguments
) -> SpiderOutput:
    """
    Take a screenshot of the webpage.
    """
    assert isinstance(setup, SpiderSetup), "Invalid setup"
    assert isinstance(arguments, SpiderFetchArguments), "Invalid arguments"

    api_key = get_api_key(setup)

    # Initialize final_result
    final_result = []
    results = None

    # Initialize spider_client
    async with get_spider_client(api_key=api_key) as spider_client:
        async for result in spider_client.screenshot(
            url=str(arguments.url),
            params=arguments.params,
            stream=False,
            content_type=arguments.content_type,
        ):
            results = result

        for page in results:
            final_result.append(
                SpiderResponse(
                    url=page["url"] if page["url"] is not None else None,
                    content=page["content"] if page["content"] is not None else None,
                    error=page["error"] if page["error"] is not None else None,
                    status=page["status"] if page["status"] is not None else None,
                    costs=page["costs"] if page["costs"] is not None else None,
                )
            )
    # Return final_result
    return SpiderOutput(result=final_result)


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def search(setup: SpiderSetup, arguments: SpiderFetchArguments) -> SpiderOutput:
    """
    Search content within the webpage.
    """
    assert isinstance(setup, SpiderSetup), "Invalid setup"
    assert isinstance(arguments, SpiderFetchArguments), "Invalid arguments"

    api_key = get_api_key(setup)

    # Initialize final_result
    final_result = []
    results = None

    # Initialize spider_client
    async with get_spider_client(api_key=api_key) as spider_client:
        async for result in spider_client.search(
            url=str(arguments.url),
            params=arguments.params,
            stream=False,
            content_type=arguments.content_type,
        ):
            results = result

        for page in results:
            final_result.append(
                SpiderResponse(
                    url=page["url"] if page["url"] is not None else None,
                    content=page["content"] if page["content"] is not None else None,
                    error=page["error"] if page["error"] is not None else None,
                    status=page["status"] if page["status"] is not None else None,
                    costs=page["costs"] if page["costs"] is not None else None,
                )
            )
    # Return final_result
    return SpiderOutput(result=final_result)
