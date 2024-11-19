from typing import Optional

from pydantic import Field

from .base_models import BaseOutput


class CloudinaryUploadOutput(BaseOutput):
    url: str = Field(..., description="The URL of the uploaded file")
    public_id: str = Field(..., description="The public ID of the uploaded file")
    meta_data: dict = Field(
        ..., description="Additional metadata from the upload response"
    )


class CloudinaryEditOutput(BaseOutput):
    transformed_url: str = Field(..., description="The transformed URL")
