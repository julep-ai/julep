from pydantic import BaseModel


class IntegrationExecutionRequest(BaseModel):
    integration_name: str
    parameters: dict


class IntegrationExecutionResponse(BaseModel):
    result: str


class IntegrationDef(BaseModel):
    provider: str
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
