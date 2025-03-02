from pydantic import Field

from .base_models import BaseOutput


class CloudinaryUploadOutput(BaseOutput):
    url: str = Field(..., description="The URL of the uploaded file")
    public_id: str = Field(..., description="The public ID of the uploaded file")
    base64: str | None = Field(
        None,
        description="The base64 encoded file if return_base64 is true",
    )
    meta_data: dict | None = Field(
        None,
        description="Additional metadata from the upload response",
    )


class CloudinaryEditOutput(BaseOutput):
    transformed_url: str = Field(..., description="The transformed URL")
    base64: str | None = Field(
        None,
        description="The base64 encoded file if return_base64 is true",
    )
