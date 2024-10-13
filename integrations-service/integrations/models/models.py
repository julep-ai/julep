from typing import Literal, Union

from pydantic import BaseModel

from .dalle_image_generator import (
    DalleImageGeneratorArguments,
    DalleImageGeneratorSetup,
)
from .duckduckgo_search import DuckDuckGoSearchExecutionArguments
from .hacker_news import HackerNewsExecutionArguments
from .weather import WeatherExecutionArguments, WeatherExecutionSetup
from .wikipedia import WikipediaExecutionArguments

ExecuteIntegrationArguments = Union[
    WikipediaExecutionArguments,
    DuckDuckGoSearchExecutionArguments,
    DalleImageGeneratorArguments,
    WeatherExecutionArguments,
    HackerNewsExecutionArguments,
]

ExecuteIntegrationSetup = Union[
    DalleImageGeneratorSetup,
    WeatherExecutionSetup,
]


class IntegrationExecutionRequest(BaseModel):
    setup: ExecuteIntegrationSetup | None = None
    """
    The setup parameters the integration accepts (such as API keys)
    """
    arguments: ExecuteIntegrationArguments
    """
    The arguments to pass to the integration
    """


class IntegrationExecutionResponse(BaseModel):
    result: str
    """
    The result of the integration execution
    """


class IntegrationDef(BaseModel):
    provider: (
        Literal[
            "dummy",
            "dalle_image_generator",
            "duckduckgo_search",
            "hacker_news",
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
