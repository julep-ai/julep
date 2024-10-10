from typing import Optional, Union

from pydantic import BaseModel

from .brave import BraveSearchArguments, BraveSearchOutput, BraveSearchSetup
from .browserbase import (
    BrowserBaseLoadArguments,
    BrowserBaseLoadOutput,
    BrowserBaseSetup,
)
from .email import EmailArguments, EmailOutput, EmailSetup
from .hacker_news import HackerNewsFetchArguments, HackerNewsFetchOutput
from .spider import SpiderFetchArguments, SpiderFetchOutput, SpiderSetup
from .weather import WeatherGetArguments, WeatherGetOutput, WeatherSetup
from .wikipedia import WikipediaSearchArguments, WikipediaSearchOutput

ExecutionSetup = Union[
    EmailSetup,
    SpiderSetup,
    WeatherSetup,
    BraveSearchSetup,
    BrowserBaseSetup,
]

ExecutionArguments = Union[
    SpiderFetchArguments,
    WeatherGetArguments,
    EmailArguments,
    HackerNewsFetchArguments,
    WikipediaSearchArguments,
    BraveSearchArguments,
    BrowserBaseLoadArguments,
]

ExecutionResponse = Union[
    SpiderFetchOutput,
    WeatherGetOutput,
    EmailOutput,
    HackerNewsFetchOutput,
    WikipediaSearchOutput,
    BraveSearchOutput,
    BrowserBaseLoadOutput,
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
