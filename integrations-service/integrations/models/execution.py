from pydantic import BaseModel

from ..autogen.Tools import (
    ArxivSearchArguments,
    # Arguments
    BraveSearchArguments,
    # Setup
    BraveSearchSetup,
    BrowserbaseCompleteSessionArguments,
    BrowserbaseContextArguments,
    BrowserbaseCreateSessionArguments,
    BrowserbaseExtensionArguments,
    BrowserbaseGetSessionArguments,
    BrowserbaseGetSessionLiveUrlsArguments,
    BrowserbaseListSessionsArguments,
    BrowserbaseSetup,
    CloudinaryEditArguments,
    CloudinarySetup,
    CloudinaryUploadArguments,
    EmailArguments,
    EmailSetup,
    FfmpegSearchArguments,
    LlamaParseFetchArguments,
    LlamaParseSetup,
    RemoteBrowserArguments,
    RemoteBrowserSetup,
    SpiderFetchArguments,
    SpiderSetup,
    UnstructuredPartitionArguments,
    UnstructuredSetup,
    WeatherGetArguments,
    WeatherSetup,
    WikipediaSearchArguments,
)
from .arxiv import ArxivSearchOutput
from .brave import BraveSearchOutput
from .browserbase import (
    BrowserbaseCompleteSessionOutput,
    BrowserbaseContextOutput,
    BrowserbaseCreateSessionOutput,
    BrowserbaseExtensionOutput,
    BrowserbaseGetSessionLiveUrlsOutput,
    BrowserbaseGetSessionOutput,
    BrowserbaseListSessionsOutput,
)
from .cloudinary import CloudinaryEditOutput, CloudinaryUploadOutput
from .email import EmailOutput
from .ffmpeg import FfmpegSearchOutput
from .llama_parse import LlamaParseFetchOutput
from .remote_browser import RemoteBrowserOutput
from .spider import SpiderOutput
from .unstructured import UnstructuredParseOutput
from .weather import WeatherGetOutput
from .wikipedia import WikipediaSearchOutput


class ExecutionError(BaseModel):
    error: str
    """
    The error message of the integration execution
    """


# Setup configurations
ExecutionSetup = (
    EmailSetup
    | SpiderSetup
    | WeatherSetup
    | BraveSearchSetup
    | BrowserbaseSetup
    | RemoteBrowserSetup
    | LlamaParseSetup
    | CloudinarySetup
    | UnstructuredSetup
)

# Argument configurations
ExecutionArguments = (
    SpiderFetchArguments
    | WeatherGetArguments
    | EmailArguments
    | WikipediaSearchArguments
    | BraveSearchArguments
    | BrowserbaseCreateSessionArguments
    | BrowserbaseGetSessionArguments
    | BrowserbaseGetSessionLiveUrlsArguments
    | BrowserbaseCompleteSessionArguments
    | BrowserbaseContextArguments
    | BrowserbaseExtensionArguments
    | BrowserbaseListSessionsArguments
    | RemoteBrowserArguments
    | LlamaParseFetchArguments
    | FfmpegSearchArguments
    | CloudinaryUploadArguments
    | CloudinaryEditArguments
    | ArxivSearchArguments
    | UnstructuredPartitionArguments
)

ExecutionResponse = (
    WeatherGetOutput
    | EmailOutput
    | WikipediaSearchOutput
    | BraveSearchOutput
    | BrowserbaseCreateSessionOutput
    | BrowserbaseGetSessionOutput
    | BrowserbaseGetSessionLiveUrlsOutput
    | BrowserbaseCompleteSessionOutput
    | BrowserbaseContextOutput
    | BrowserbaseExtensionOutput
    | BrowserbaseListSessionsOutput
    | RemoteBrowserOutput
    | LlamaParseFetchOutput
    | FfmpegSearchOutput
    | CloudinaryEditOutput
    | CloudinaryUploadOutput
    | ExecutionError
    | ArxivSearchOutput
    | SpiderOutput
    | UnstructuredParseOutput
)


class ExecutionRequest(BaseModel):
    setup: ExecutionSetup | None
    """
    The setup parameters the integration accepts (such as API keys)
    """
    arguments: ExecutionArguments | None
    """
    The arguments to pass to the integration
    """
