import json
from typing import cast

from ...autogen.openapi_model import (
    ChatMLImageContentPart,
    ChatMLTextContentPart,
)


def content_to_json(
    content: str | list[ChatMLTextContentPart] | list[ChatMLImageContentPart] | dict,
):
    result = []
    if isinstance(content, str):
        result = [{"type": "text", "text": content}]
    elif isinstance(content, list):
        for part in content:
            m = {"type": part.type, part.type: None}
            if isinstance(part, ChatMLTextContentPart):
                m[part.type] = part.text
            elif isinstance(part, ChatMLImageContentPart):
                m[part.type] = part.image_url.model_dump()
            result.append(m)
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
