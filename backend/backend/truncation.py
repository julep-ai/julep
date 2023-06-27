from functools import lru_cache
from transformers import AutoTokenizer
from typing import Literal, Optional, TypedDict


class ChatMLMessage(TypedDict):
    name: Optional[str] = None
    role: Literal["assistant", "system", "user"]
    content: str


ChatML = list[ChatMLMessage]


def message_role_to_prefix(message: ChatMLMessage) -> str:
    match message:
        case {"role": "system", "name": name, **rest}:
            return name
        case {"role": "user", "name": name, **rest}:
            return f"person ({name})" if name else "person"
        case {"role": "assistant", "name": name, **rest}:
            return f"me ({name})" if name else "me"


def to_prompt(
    messages: ChatML,
    suffix: str,
    bos: str = "<|section|>",
    eos: str = "<|endsection|>",
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
            f"{bos}{message_role_to_prefix(message)}\n{message['content']}{eos}"
            for message in messages
        ]
    )

    return prompt + suffix


tokenizer_id = "julep-ai/samantha-33b"
tokenizer = AutoTokenizer.from_pretrained(tokenizer_id, use_fast=False)


@lru_cache
def count_tokens(prompt: str):
    tokens = tokenizer.encode(prompt)
    return len(tokens)


def truncate(
    chatml: ChatML, max_tokens: int = 1500, keep_roles: list[str] = ["system"]
) -> ChatML:
    chatml_with_idx = list(enumerate(chatml))
    chatml_to_keep = [c for c in chatml_with_idx if c[1]["role"] in keep_roles]
    budget = (
        max_tokens
        - sum([count_tokens(to_prompt([c[1]], suffix="")) for c in chatml_to_keep])
        - count_tokens("<|section|>me (Samantha)\n")
    )

    assert budget > 0, "keep_roles messages exhaust tokens"

    remaining = [c for c in chatml_with_idx if c[1]["role"] not in keep_roles]
    for i, c in reversed(remaining):
        c_len = count_tokens(to_prompt([c], suffix=""))

        if budget < c_len:
            break

        budget -= c_len
        chatml_to_keep.append((i, c))

    sorted_kept = sorted(chatml_to_keep, key=lambda x: x[0])
    return [c for _, c in sorted_kept]


# chatml = [
#    {"role": "system", "content": f"SYSTEM"},
#    *[
#        {"role": "user", "content": f"Hello {i}"}
#        for i in range(500)
#    ]
# ]

# truncate(chatml, max_tokens=100)
