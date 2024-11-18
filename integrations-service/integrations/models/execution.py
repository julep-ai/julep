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
    LlamaParseFetchArguments,
    LlamaParseSetup,
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
from .llama_parse import LlamaParseFetchOutput
from .remote_browser import RemoteBrowserOutput
from .spider import SpiderFetchOutput
from .weather import WeatherGetOutput
from .wikipedia import WikipediaSearchOutput


class ExecutionError(BaseModel):
    error: str
    """
    The error message of the integration execution
    """


ExecutionSetup = Union[
    EmailSetup,
    SpiderSetup,
    WeatherSetup,
    BraveSearchSetup,
    BrowserbaseSetup,
    RemoteBrowserSetup,
    LlamaParseSetup,
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
    LlamaParseFetchArguments,
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
    LlamaParseFetchOutput,
    ExecutionError,
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
