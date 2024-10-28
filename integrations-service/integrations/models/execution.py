from typing import Optional, Union

from pydantic import BaseModel

from .brave import BraveSearchArguments, BraveSearchOutput, BraveSearchSetup
from .email import EmailArguments, EmailOutput, EmailSetup
from .spider import SpiderFetchArguments, SpiderFetchOutput, SpiderSetup
from .weather import WeatherGetArguments, WeatherGetOutput, WeatherSetup
from .wikipedia import WikipediaSearchArguments, WikipediaSearchOutput

ExecutionSetup = Union[
    EmailSetup,
    SpiderSetup,
    WeatherSetup,
    BraveSearchSetup,
]

ExecutionArguments = Union[
    SpiderFetchArguments,
    WeatherGetArguments,
    EmailArguments,
    WikipediaSearchArguments,
    BraveSearchArguments,
]

ExecutionResponse = Union[
    SpiderFetchOutput,
    WeatherGetOutput,
    EmailOutput,
    WikipediaSearchOutput,
    BraveSearchOutput,
]


class ExecutionRequest(BaseModel):
    setup: Optional[ExecutionSetup]
    """
    The setup parameters the integration accepts (such as API keys)
    """
    arguments: ExecutionArguments
    """
    The arguments to pass to the integration
    """
