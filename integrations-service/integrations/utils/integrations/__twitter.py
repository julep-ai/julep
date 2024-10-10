import os

from langchain_community.document_loaders import TwitterTweetLoader


async def twitter(arguments: dict) -> str:
    """
    Loads tweets from specified Twitter users and returns them as formatted string.
    """
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        raise ValueError("Twitter API bearer token is not set")

    twitter_users = arguments.get("twitter_users")
    if not twitter_users:
        raise ValueError("Twitter users parameter is required for Twitter loader")

    number_tweets = arguments.get("number_tweets", 50)

    loader = TwitterTweetLoader.from_bearer_token(
        oauth2_bearer_token=bearer_token,
        twitter_users=twitter_users,
        number_tweets=number_tweets,
    )

    documents = loader.load()

    # Format the results as a string
    result = "\n\n".join(
        [f"Tweet: {doc.page_content}\nMetadata: {doc.metadata}" for doc in documents]
    )
    return result
