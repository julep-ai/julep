from openai import AsyncClient
from tenacity import retry, stop_after_attempt, wait_fixed


client = AsyncClient()


@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
async def generate(
    messages: list[dict],
    client: AsyncClient = client,
    model: str = "gpt-4-turbo",
    **kwargs
) -> dict:
    result = await client.chat.completions.create(
        model=model, messages=messages, **kwargs
    )

    result = result.choices[0].message.__dict__

    return result
