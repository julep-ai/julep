from ..models import ExecuteIntegrationParams
from .integrations.dalle_image_generator import dalle_image_generator
from .integrations.duckduckgo_search import duckduckgo_search
from .integrations.twitter import twitter
from .integrations.wikipedia import wikipedia


async def execute_integration(
    integration_name: str, parameters: ExecuteIntegrationParams
) -> str:
    match integration_name:
        case "duckduckgo_search":
            return await duckduckgo_search(parameters)
        case "dalle_image_generator":
            return await dalle_image_generator(parameters)
        case "twitter_loader":
            return await twitter(parameters)
        case "wikipedia_query":
            return await wikipedia(parameters)
        case _:
            raise ValueError(f"Unknown integration: {integration_name}")
