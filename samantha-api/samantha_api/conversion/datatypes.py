from typing import Optional, Literal, TypedDict


ChatMLMessage = TypedDict(
    "ChatMLMessage",
    {
        "name": Optional[str],
        "role": Literal["assistant", "system", "user", "function_call"],
        "content": str,
        "continue": Optional[bool],
    },
)

ChatML = list[ChatMLMessage]
