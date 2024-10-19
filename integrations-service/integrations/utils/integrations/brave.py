from langchain_community.tools import BraveSearch
from tenacity import retry, stop_after_attempt, wait_exponential

from ...models import BraveSearchArguments, BraveSearchOutput, BraveSearchSetup


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def search(
    setup: BraveSearchSetup, arguments: BraveSearchArguments
) -> BraveSearchOutput:
    """
    Searches Brave Search with the provided query.
    """

    assert isinstance(setup, BraveSearchSetup), "Invalid setup"
    assert isinstance(arguments, BraveSearchArguments), "Invalid arguments"

    tool = BraveSearch.from_api_key(api_key=setup.api_key, search_kwargs={"count": 3})

    result = tool.run(arguments.query)
    return BraveSearchOutput(result=result)
