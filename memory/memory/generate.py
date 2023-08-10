import os

import httpx

from .types import ChatML
from .utils import (
    to_prompt,
)

############
## Consts ##
############

COMPLETION_URL: str = os.environ.get(
    "COMPLETION_URL", "https://julep-samantha-33b.ngrok.dev/v1/completions"
)
AGENT_NAME: str = "Samantha"

# TODO: Add generate cache using the `lm_cache` relation in cozo
#   Match cache if xx_hash64(json.dumps(chatml)) == lm_cache.chatml_hash
#   OR if embedding(chatml) ~ lm_cache.embedding (confidence: 0.95)
#   If cache hit, return lm_cache.response

async def generate(
    messages: ChatML,
    stop: list[str] = ["<"],
    max_tokens: int = 250,
    temperature: float = 0.4,
    model: str = "julep-ai/samantha-33b",
    frequency_penalty=1.0,
    presence_penalty=0.75,
    best_of=2,
    prompt_settings: dict = {},
) -> dict:
    prompt = to_prompt(messages, **prompt_settings)
    print("***", prompt)

    async with httpx.AsyncClient(timeout=httpx.Timeout(60)) as client:
        resp = await client.post(
            COMPLETION_URL,
            json={
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "stop": stop,
                "temperature": temperature,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "best_of": best_of,
            },
        )

    resp.raise_for_status()

    return resp.json()
