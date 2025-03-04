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
    return setup.spider_api_key if setup.spider_api_key != "DEMO_API_KEY" else spider_api_key


def create_spider_response(pages: list[dict]) -> list[SpiderResponse]:
    return [
        SpiderResponse(
            url=page.get("url"),
            content=(page.get("content")),
            error=page.get("error"),
            status=page.get("status"),
            costs=page.get("costs"),
        )
        for page in pages
    ]


async def execute_spider_method(
    method_name: str,
    setup: SpiderSetup,
    arguments: SpiderFetchArguments,
) -> SpiderOutput:
    api_key = get_api_key(setup)
    final_result = []
    results = None

    try:
        async with get_spider_client(api_key=api_key) as spider_client:
            async for result in getattr(spider_client, method_name)(
                url=str(arguments.url),
                params=arguments.params,
                stream=False,
                content_type=arguments.content_type,
            ):
                results = result

        if results is None:
            msg = "No results found"
            raise ValueError(msg)
        final_result = create_spider_response(results)
    except Exception as e:
        # Log the exception or handle it as needed
        msg = f"Error executing spider method '{method_name}': {e}"
        raise RuntimeError(msg)

    return SpiderOutput(result=final_result)


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
    return await execute_spider_method("crawl_url", setup, arguments)


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
    return await execute_spider_method("links", setup, arguments)


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def screenshot(setup: SpiderSetup, arguments: SpiderFetchArguments) -> SpiderOutput:
    """
    Take a screenshot of the webpage.
    """
    assert isinstance(setup, SpiderSetup), "Invalid setup"
    assert isinstance(arguments, SpiderFetchArguments), "Invalid arguments"
    return await execute_spider_method("screenshot", setup, arguments)


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
    return await execute_spider_method("search", setup, arguments)
