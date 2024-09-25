from ..models import ExecuteIntegrationArguments
from .integrations.dalle_image_generator import dalle_image_generator
from .integrations.duckduckgo_search import duckduckgo_search
from .integrations.twitter import twitter
from .integrations.wikipedia import wikipedia


async def execute_integration(
    integration_name: str, arguments: ExecuteIntegrationArguments
) -> str:
    match integration_name:
        case "duckduckgo_search":
            return await duckduckgo_search(arguments)
        case "dalle_image_generator":
            return await dalle_image_generator(arguments)
        case "twitter_loader":
            return await twitter(arguments)
        case "wikipedia_query":
            return await wikipedia(arguments)
        case _:
            raise ValueError(f"Unknown integration: {integration_name}")
