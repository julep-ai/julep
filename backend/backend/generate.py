import os
import httpx

# import spacy
# from spacy.lang.en import English
# from collections import deque
# import itertools as it
# import random
# from threading import Thread
from typing import Literal, Optional, TypedDict


COMPLETION_URL = os.environ["COMPLETION_URL"]
HTTP_TIMEOUT = httpx.Timeout(timeout=300.0)


# import torch
# from transformers import (
#     AutoModelForCausalLM,
#     AutoTokenizer,
#     StoppingCriteria,
#     StoppingCriteriaList,
#     TextIteratorStreamer,
# )


# spacy.prefer_gpu()
# nlp = English()


# ###########
# ## Types ##
# ###########


class AssistantOutput(TypedDict):
    session_id: str
    assistant_output: str


class ChatMLMessage(TypedDict):
    name: Optional[str]
    role: Literal["assistant", "system", "user"]
    content: str


ChatML = list[ChatMLMessage]


AGENT_NAME: str = "Samantha"
PERSON_NAME: str = "Diwank"


def message_role_to_prefix(message: ChatMLMessage) -> str:
    match message:
        case {"role": "system", "name": name, **rest}:
            return name
        case {"role": "user", **rest}:
            name = rest.get("name", None)
            return f"person ({name})" if name else "person"
        case {"role": "assistant", "name": name, **rest}:
            return f"me ({name})" if name else "me"


def to_prompt(
    messages: ChatML,
    bos: str = "<|section|>",
    eos: str = "<|endsection|>",
    suffix: str = f"\n<|section|>me ({AGENT_NAME})\n",
) -> str:
    # Input format:
    # [
    #     {"role": "system", "name": "situation", "content": "I am talking to Diwank"},
    #     {"role": "assistant", "name": "Samantha", "content": "Hey Diwank"},
    #     {"role": "user", "name": "Diwank", "content": "Hey!"},
    # ]

    # Output format:
    #
    # <|section|>situation
    # I am talking to Diwank<|endsection|>
    # <|section|>me (Samantha)
    # Hey Diwank<|endsection|>
    # <|section|>person (Diwank)
    # Hey<|endsection|>
    # <|section|>me (Samantha)\n

    prompt = "\n".join(
        [
            f"{bos}{message_role_to_prefix(message)}\n{message['content'].strip()}{eos}"
            for message in messages
        ]
    )

    return prompt + suffix


async def generate(
    messages: ChatML,
    stop: list[str] = [],
    max_tokens: int = 250,
    temperature: float = 0.45,
    model: str = "julep-ai/samantha-33b",
    frequency_penalty=1.25,
    presence_penalty=0.75,
    best_of=2,
    prompt_settings: dict = {},
    completion_url: str = COMPLETION_URL,
) -> dict:
    prompt = to_prompt(messages, **prompt_settings)
    print("***", prompt)

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.post(
            completion_url,
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


async def generate_with_memory(
    user_input: str,
    email: str,
    name: str,
    conversation_id: str,
    situation: str,
    completion_url: str = COMPLETION_URL,
) -> AssistantOutput:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.post(
            completion_url,
            json={
                "email": email,
                "name": name,
                "vocode_conversation_id": conversation_id,
                "user_input": user_input,
                "situation": situation,
            },
        )
    resp.raise_for_status()

    return resp.json()
