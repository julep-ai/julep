from typing import Optional

from pydantic import Field

from .base_models import BaseOutput


class CloudinaryOutput(BaseOutput):
    result: bool = Field(..., description="The result of the Cloudinary command")
