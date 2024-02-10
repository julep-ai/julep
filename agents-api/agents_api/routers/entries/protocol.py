from pydantic import BaseModel
from agents_api.common.protocol.entries import Entry


class EntriesRequest(BaseModel):
    entries: list[Entry]
