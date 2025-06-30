import json

from beartype import beartype
from langchain_community.tools import BraveSearch
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import BraveSearchArguments, BraveSearchSetup
from ...models import BraveSearchOutput, SearchResult


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def search(setup: BraveSearchSetup, arguments: BraveSearchArguments) -> BraveSearchOutput:
    """
    Searches Brave Search with the provided query.
    """

    tool = BraveSearch.from_api_key(api_key=setup.brave_api_key, search_kwargs={"count": 3})

    result = tool.run(arguments.query)

    try:
        parsed_result = [SearchResult(**item) for item in json.loads(result)]
    except json.JSONDecodeError as e:
        msg = "Malformed JSON response from Brave Search"
        raise ValueError(msg) from e

    return BraveSearchOutput(result=parsed_result)
