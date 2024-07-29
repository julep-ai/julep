import json
from typing import Literal
from uuid import UUID

from pydantic import Field, computed_field

from ...autogen.openapi_model import (
    ChatMLImageContentPart,
    ChatMLTextContentPart,
)
from ...autogen.openapi_model import (
    Entry as BaseEntry,
)

EntrySource = Literal["api_request", "api_response", "internal", "summarizer"]
Tokenizer = Literal["character_count"]


LOW_IMAGE_TOKEN_COUNT = 85
HIGH_IMAGE_TOKEN_COUNT = 85 + 4 * 170


class Entry(BaseEntry):
    """Represents an entry in the system, encapsulating all necessary details such as ID, session ID, source, role, and content among others."""

    session_id: UUID
    token_count: int
    tokenizer: str = Field(default="character_count")

    @computed_field
    @property
    def token_count(self) -> int:
        """Calculates the token count based on the content's character count. The tokenizer 'character_count' divides the length of the content by 3.5 to estimate the token count. Raises NotImplementedError for unknown tokenizers."""
        if self.tokenizer == "character_count":
            content_length = 0
            if isinstance(self.content, str):
                content_length = len(self.content)
            elif isinstance(self.content, dict):
                content_length = len(json.dumps(self.content))
            elif isinstance(self.content, list):
                for part in self.content:
                    if isinstance(part, ChatMLTextContentPart):
                        content_length += len(part.text)
                    elif isinstance(part, ChatMLImageContentPart):
                        content_length += (
                            LOW_IMAGE_TOKEN_COUNT
                            if part.image_url.detail == "low"
                            else HIGH_IMAGE_TOKEN_COUNT
                        )

            # Divide the content length by 3.5 to estimate token count based on character count.
            return int(content_length // 3.5)

        raise NotImplementedError(f"Unknown tokenizer: {self.tokenizer}")
