from typing import Optional

from pydantic import Field

from .base_models import BaseOutput


class FfmpegSearchOutput(BaseOutput):
    fileoutput: Optional[str] = Field(
        None, description="The output file from the Ffmpeg command"
    )
    result: bool = Field(..., description="Whether the Ffmpeg command was successful")
    mime_type: Optional[str] = Field(
        None, description="The MIME type of the output file"
    )
