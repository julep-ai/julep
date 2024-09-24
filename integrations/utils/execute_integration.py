from .integrations import (
    dalle_image_generator,
    duckduckgo_search,
    twitter_loader,
    wikipedia_query,
)


async def execute_integration(integration_name: str, parameters: dict) -> str:
    match integration_name:
        case "duckduckgo_search":
            return await duckduckgo_search(parameters)
        case "dalle_image_generator":
            return await dalle_image_generator(parameters)
        case "twitter_loader":
            return await twitter_loader(parameters)
        case "wikipedia_query":
            return await wikipedia_query(parameters)
        case _:
            raise ValueError(f"Unknown integration: {integration_name}")
