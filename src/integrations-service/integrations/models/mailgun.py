from pydantic import Field

from .base_models import BaseOutput


class MailgunSendEmailOutput(BaseOutput):
    success: bool = Field(..., description="Whether the email was sent successfully")
    error: str | None = Field(
        None, description="The error message if the email was not sent successfully"
    )
