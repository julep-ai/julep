from pydantic import Field

from .base_models import BaseOutput


class RemoteBrowserOutput(BaseOutput):
    output: str | None = Field(None, description="The output of the action")
    error: str | None = Field(None, description="The error of the action")
    base64_image: str | None = Field(
        None, description="The base64 encoded image of the action"
    )
    system: str | None = Field(None, description="The system output of the action")
