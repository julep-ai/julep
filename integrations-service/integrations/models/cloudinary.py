from typing import Optional

from pydantic import Field

from .base_models import BaseOutput


class CloudinaryOutput(BaseOutput):
    transformed_url: str = Field(..., description="The transformed URL")
