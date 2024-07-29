from openai import AsyncOpenAI

from ..env import model_api_key, model_inference_url, openai_api_key

openai_client = AsyncOpenAI(api_key=openai_api_key)

julep_client = AsyncOpenAI(
    base_url=model_inference_url,
    api_key=model_api_key,
)
