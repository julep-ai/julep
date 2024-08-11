from tenacity import retry, stop_after_attempt, wait_fixed

from agents_api.clients.litellm import acompletion


@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
async def generate(
    messages: list[dict],
    model: str = "gpt-4-turbo",
    **kwargs,
) -> dict:
    result = await acompletion(
        model=model,
        messages=messages,
        **kwargs,
    )

    return result.choices[0].message.json()
