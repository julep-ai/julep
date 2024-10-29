from pydantic import Field

from .base_models import BaseOutput


class BraveSearchOutput(BaseOutput):
    result: str = Field(..., description="The result of the Brave Search")
