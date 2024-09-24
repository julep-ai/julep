from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.document_loaders import TwitterTweetLoader
import os


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

async def duckduckgo_search(parameters: dict) -> str:
    search = DuckDuckGoSearchRun()
    query = parameters.get("query")
    if not query:
        raise ValueError("Query parameter is required for DuckDuckGo search")
    return search.run(query)


async def dalle_image_generator(parameters: dict) -> str:
    # FIXME: Fix OpenAI API Key error

    dalle = DallEAPIWrapper()
    prompt = parameters.get("prompt")
    if not prompt:
        raise ValueError(
            "Prompt parameter is required for DALL-E image generation")
    return dalle.run(prompt)


async def twitter_loader(parameters: dict) -> str:
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        raise ValueError("Twitter API bearer token is not set")

    twitter_users = parameters.get("twitter_users")
    if not twitter_users:
        raise ValueError(
            "Twitter users parameter is required for Twitter loader")

    number_tweets = parameters.get("number_tweets", 50)

    loader = TwitterTweetLoader.from_bearer_token(
        oauth2_bearer_token=bearer_token,
        twitter_users=twitter_users,
        number_tweets=number_tweets,
    )

    documents = loader.load()

    # Format the results as a string
    result = "\n\n".join(
        [f"Tweet: {doc.page_content}\nMetadata: {doc.metadata}" for doc in documents])
    return result


async def wikipedia_query(parameters: dict) -> str:
    query = parameters.get("query")
    if not query:
        raise ValueError("Query parameter is required for Wikipedia search")

    load_max_docs = parameters.get("load_max_docs", 2)

    loader = WikipediaLoader(query=query, load_max_docs=load_max_docs)
    documents = loader.load()

    # Format the results as string
    result = "\n\n".join([
        f"Title: {doc.metadata['title']}\n"
        f"Summary: {doc.metadata['summary']}\n"
        f"Content: {doc.page_content}..."
        for doc in documents
    ])
    return result
