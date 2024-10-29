from typing import Literal

from pydantic import BaseModel


class IntegrationExecutionResponse(BaseModel):
    result: str
    """
    The result of the integration execution
    """


class IntegrationDef(BaseModel):
    provider: (
        Literal[
            "dummy",
            "weather",
            "wikipedia",
            "twitter",
            "web_base",
            "requests",
            "gmail",
            "tts_query",
        ]
        | None
    ) = None
    """
    The provider of the integration
    """
    method: str | None = None
    """
    The specific method of the integration to call
    """
    description: str | None = None
    """
    Optional description of the integration
    """
    setup: dict | None = None
    """
    The setup parameters the integration accepts
    """
    arguments: dict | None = None
    """
    The arguments to pre-apply to the integration call
    """
