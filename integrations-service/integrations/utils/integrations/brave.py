import json

from beartype import beartype
from langchain_community.tools import BraveSearch
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import BraveSearchArguments, BraveSearchSetup
from ...env import brave_api_key  # Import env to access environment variables
from ...models import BraveSearchOutput, SearchResult


@beartype
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

    # Check if the setup.api_key is 'DEMO_API_KEY' and load from environment if true
    if setup.api_key == "DEMO_API_KEY":
        setup.api_key = brave_api_key

    tool = BraveSearch.from_api_key(api_key=setup.api_key, search_kwargs={"count": 3})

    result = tool.run(arguments.query)

    try:
        parsed_result = [SearchResult(**item) for item in json.loads(result)]
    except json.JSONDecodeError as e:
        raise ValueError("Malformed JSON response from Brave Search") from e

    return BraveSearchOutput(result=parsed_result)
