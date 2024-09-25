from ..models import ExecuteIntegrationArguments, ExecuteIntegrationSetup
from .integrations.dalle_image_generator import dalle_image_generator
from .integrations.duckduckgo_search import duckduckgo_search
from .integrations.hacker_news import hacker_news
from .integrations.weather import weather
from .integrations.wikipedia import wikipedia


async def execute_integration(
    provider: str,
    setup: ExecuteIntegrationSetup | None,
    arguments: ExecuteIntegrationArguments,
) -> str:
    match provider:
        case "duckduckgo_search":
            return await duckduckgo_search(arguments=arguments)
        case "dalle_image_generator":
            return await dalle_image_generator(setup=setup, arguments=arguments)
        case "wikipedia":
            return await wikipedia(arguments=arguments)
        case "weather":
            return await weather(setup=setup, arguments=arguments)
        case "hacker_news":
            return await hacker_news(arguments=arguments)
        case _:
            raise ValueError(f"Unknown integration: {provider}")
