from pydantic import BaseModel
from memory_api.common.protocol.entries import Entry


class EntriesRequest(BaseModel):
    entries: list[Entry]
