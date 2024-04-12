from typing import Literal

from pydantic import BaseModel


class AgentDefaultSettings(BaseModel):
    temperature: float = 0.0
    top_p: float = 1.0
    repetition_penalty: float = 1.0
    length_penalty: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    min_p: float = 0.01
