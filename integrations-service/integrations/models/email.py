from pydantic import Field

from .base_models import BaseOutput


class EmailOutput(BaseOutput):
    success: bool = Field(..., description="Whether the email was sent successfully")
