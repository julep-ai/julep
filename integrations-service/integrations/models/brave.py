from pydantic import Field

from .base_models import (
    BaseArguments,
    BaseOutput,
    BaseSetup,
)


class BraveSearchSetup(BaseSetup):
    api_key: str = Field(..., description="The api key for Brave Search")


class BraveSearchArguments(BaseArguments):
    query: str = Field(..., description="The search query for searching with Brave")


class BraveSearchOutput(BaseOutput):
    result: str = Field(..., description="The result of the Brave Search")
