import json
from typing import cast

from beartype import beartype

from ...autogen.openapi_model import (
    ChatMLImageContentPart,
    ChatMLTextContentPart,
)


@beartype
def content_to_json(
    content: str | list[dict] | dict,
) -> list[dict]:
    if isinstance(content, str):
        result = [{"type": "text", "text": content}]
    elif isinstance(content, list):
        result = content
    elif isinstance(content, dict):
        result = [{"type": "text", "text": json.dumps(content, indent=4)}]

    return result


def stringify_content(
    msg: str | list[ChatMLTextContentPart] | list[ChatMLImageContentPart] | dict,
) -> str:
    content = ""
    if isinstance(msg, list):
        content = " ".join([part.text for part in msg if part.type == "text"])
    elif isinstance(msg, str):
        content = msg
    elif isinstance(msg, dict) and msg["type"] == "text":
        content = cast(str, msg["text"])

    return content
