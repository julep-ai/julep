from beartype import beartype
from spider import AsyncSpider
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import SpiderFetchArguments, SpiderSetup
from ...models import SpiderOutput, SpiderResponse


@beartype
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


@beartype
async def execute_spider_method(
    method_name: str,
    setup: SpiderSetup,
    arguments: SpiderFetchArguments,
) -> SpiderOutput:
    api_key = setup.spider_api_key
    # Initialize the final result list
    final_result = []
    # Initialize the results variable
    results = None

    try:
        async with AsyncSpider(api_key=api_key) as spider_client:
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
    return await execute_spider_method("search", setup, arguments)
