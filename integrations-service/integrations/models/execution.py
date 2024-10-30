from typing import Optional, Union

from pydantic import BaseModel

from ..autogen.Tools import (
    # Setup
    BraveSearchSetup,
    SpiderSetup,
    EmailSetup,
    WeatherSetup,
    BrowserbaseSetup,
    # Arguments
    BraveSearchArguments,
    EmailArguments,
    SpiderFetchArguments,
    WeatherGetArguments,
    WikipediaSearchArguments,
    BrowserbaseCompleteSessionArguments,
    BrowserbaseContextArguments,
    BrowserbaseCreateSessionArguments,
    BrowserbaseGetSessionArguments,
    BrowserbaseGetSessionLiveUrlsArguments,
    BrowserbaseGetSessionConnectUrlArguments,
    BrowserbaseExtensionArguments,
    BrowserbaseListSessionsArguments,
    RemoteBrowserArguments,
)
from .brave import BraveSearchOutput
from .email import EmailOutput
from .spider import SpiderFetchOutput
from .weather import WeatherGetOutput
from .wikipedia import WikipediaSearchOutput
from .remote_browser import RemoteBrowserOutput
from .browserbase import (
    BrowserbaseCreateSessionOutput,
    BrowserbaseListSessionsOutput,
    BrowserbaseCompleteSessionOutput,
    BrowserbaseGetSessionOutput,
    BrowserbaseContextOutput,
    BrowserbaseGetSessionLiveUrlsOutput,
    BrowserbaseGetSessionConnectUrlOutput,
    BrowserbaseExtensionOutput,
)

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
    BrowserbaseCompleteSessionArguments,
    BrowserbaseContextArguments,
    BrowserbaseCreateSessionArguments,
    BrowserbaseGetSessionArguments,
    BrowserbaseGetSessionLiveUrlsArguments,
    BrowserbaseGetSessionConnectUrlArguments,
    BrowserbaseExtensionArguments,
    BrowserbaseListSessionsArguments,
    RemoteBrowserArguments,
]

ExecutionResponse = Union[
    SpiderFetchOutput,
    WeatherGetOutput,
    EmailOutput,
    WikipediaSearchOutput,
    BraveSearchOutput,
    BrowserbaseCreateSessionOutput,
    RemoteBrowserOutput,
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
