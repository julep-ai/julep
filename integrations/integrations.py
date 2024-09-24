from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper


async def execute_integration(integration_name: str, parameters: dict) -> str:
    if integration_name == "duckduckgo_search":
        return await duckduckgo_search(parameters)
    elif integration_name == "dalle_image_generator":
        return await dalle_image_generator(parameters)
    else:
        raise ValueError(f"Unknown integration: {integration_name}")


async def duckduckgo_search(parameters: dict) -> str:
    search = DuckDuckGoSearchRun()
    query = parameters.get("query")
    if not query:
        raise ValueError("Query parameter is required for DuckDuckGo search")
    return search.run(query)


async def dalle_image_generator(parameters: dict) -> str:
    dalle = DallEAPIWrapper()
    prompt = parameters.get("prompt")
    if not prompt:
        raise ValueError(
            "Prompt parameter is required for DALL-E image generation")
    return dalle.run(prompt)
