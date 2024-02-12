from typing import cast, Optional, Literal, TypedDict


ValidRole = Literal["assistant", "system", "user", "function_call"]
ChatMLMessage = TypedDict(
    "ChatMLMessage",
    {
        "name": Optional[str],
        "role": Optional[ValidRole],
        "content": Optional[str],
        "continue": Optional[bool],
    },
)


def make_chatml_message(
    role: Optional[ValidRole] = None,
    name: Optional[str] = None,
    content: Optional[str] = None,
    continue_: Optional[bool] = None,
) -> ChatMLMessage:
    # Make sure not all of the fields are None
    assert any((role, name, content, continue_))

    return cast(
        ChatMLMessage,
        {
            "role": role,
            "name": name,
            "content": content,
            "continue": continue_,
        },
    )


ChatML = list[ChatMLMessage]
