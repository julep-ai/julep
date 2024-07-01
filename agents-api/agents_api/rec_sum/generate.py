from tenacity import retry, stop_after_attempt, wait_fixed
from agents_api.env import model_inference_url, model_api_key
from agents_api.model_registry import JULEP_MODELS
from litellm import acompletion


@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
async def generate(
    messages: list[dict],
    model: str = "gpt-4-turbo",
    **kwargs,
) -> dict:
    base_url, api_key = None, None
    if model in JULEP_MODELS:
        base_url, api_key = model_inference_url, model_api_key
        model = f"openai/{model}"

    result = await acompletion(
        model=model,
        messages=messages,
        base_url=base_url,
        api_key=api_key,
    )

    return result.choices[0].message.json()
