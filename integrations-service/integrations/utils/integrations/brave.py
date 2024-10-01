from langchain_community.tools import BraveSearch

from ...models import BraveSearchArguments, BraveSearchOutput, BraveSearchSetup


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
