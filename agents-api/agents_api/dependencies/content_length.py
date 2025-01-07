from fastapi import Header

from ..env import max_payload_size


async def valid_content_length(content_length: int = Header(..., lt=max_payload_size)):
    return content_length
