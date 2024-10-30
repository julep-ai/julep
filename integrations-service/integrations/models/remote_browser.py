from typing import Any

from pydantic import Field

from .base_models import BaseOutput


class RemoteBrowserOutput(BaseOutput):
    result: Any = Field(..., description="The result of the action")
