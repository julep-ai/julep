from pydantic import EmailStr, Field

from .base_models import (
    BaseArguments,
    BaseOutput,
    BaseSetup,
)


class EmailSetup(BaseSetup):
    host: str = Field(..., description="The host of the email server")
    port: int = Field(..., description="The port of the email server")
    user: str = Field(..., description="The username of the email server")
    password: str = Field(..., description="The password of the email server")


class EmailArguments(BaseArguments):
    to: EmailStr = Field(..., description="The email address to send the email to")
    from_: EmailStr = Field(
        ..., alias="from", description="The email address to send the email from"
    )
    subject: str = Field(..., description="The subject of the email")
    body: str = Field(..., description="The body of the email")


class EmailOutput(BaseOutput):
    success: bool = Field(..., description="Whether the email was sent successfully")
