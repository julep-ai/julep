from pydantic import Field

from .base_models import BaseOutput


class FfmpegSearchOutput(BaseOutput):
    fileoutput: str | None = Field(None, description="The output file from the Ffmpeg command")
    result: bool = Field(..., description="Whether the Ffmpeg command was successful")
    mime_type: str | None = Field(None, description="The MIME type of the output file")
