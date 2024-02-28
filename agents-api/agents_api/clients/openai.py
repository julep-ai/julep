from openai import AsyncOpenAI
from ..env import generation_auth_token, generation_url


client = AsyncOpenAI(
    api_key=generation_auth_token,
    base_url=generation_url,
)
