from typing import Optional, Union

from pydantic import BaseModel

from ..autogen.Tools import (
    # Arguments
    BraveSearchArguments,
    # Setup
    BraveSearchSetup,
    BrowserbaseCompleteSessionArguments,
    BrowserbaseContextArguments,
    BrowserbaseCreateSessionArguments,
    BrowserbaseExtensionArguments,
    BrowserbaseGetSessionArguments,
    BrowserbaseGetSessionConnectUrlArguments,
    BrowserbaseGetSessionLiveUrlsArguments,
    BrowserbaseListSessionsArguments,
    BrowserbaseSetup,
    EmailArguments,
    EmailSetup,
    RemoteBrowserArguments,
    RemoteBrowserSetup,
    SpiderFetchArguments,
    SpiderSetup,
    WeatherGetArguments,
    WeatherSetup,
    WikipediaSearchArguments,
)
from .brave import BraveSearchOutput
from .browserbase import (
    BrowserbaseCompleteSessionOutput,
    BrowserbaseContextOutput,
    BrowserbaseCreateSessionOutput,
    BrowserbaseExtensionOutput,
    BrowserbaseGetSessionConnectUrlOutput,
    BrowserbaseGetSessionLiveUrlsOutput,
    BrowserbaseGetSessionOutput,
    BrowserbaseListSessionsOutput,
)
from .email import EmailOutput
from .remote_browser import RemoteBrowserOutput
from .spider import SpiderFetchOutput
from .weather import WeatherGetOutput
from .wikipedia import WikipediaSearchOutput

ExecutionSetup = Union[
    EmailSetup,
    SpiderSetup,
    WeatherSetup,
    BraveSearchSetup,
    BrowserbaseSetup,
    RemoteBrowserSetup,
]

ExecutionArguments = Union[
    SpiderFetchArguments,
    WeatherGetArguments,
    EmailArguments,
    WikipediaSearchArguments,
    BraveSearchArguments,
    BrowserbaseCreateSessionArguments,
    BrowserbaseGetSessionArguments,
    BrowserbaseGetSessionConnectUrlArguments,
    BrowserbaseGetSessionLiveUrlsArguments,
    BrowserbaseCompleteSessionArguments,
    BrowserbaseContextArguments,
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
    BrowserbaseGetSessionOutput,
    BrowserbaseGetSessionConnectUrlOutput,
    BrowserbaseGetSessionLiveUrlsOutput,
    BrowserbaseCompleteSessionOutput,
    BrowserbaseContextOutput,
    BrowserbaseExtensionOutput,
    BrowserbaseListSessionsOutput,
    RemoteBrowserOutput,
]


class ExecutionRequest(BaseModel):
    setup: Optional[ExecutionSetup]
    """
    The setup parameters the integration accepts (such as API keys)
    """
    arguments: Optional[ExecutionArguments]
    """
    The arguments to pass to the integration
    """
