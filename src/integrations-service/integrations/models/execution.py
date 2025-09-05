from pydantic import BaseModel

from ..autogen.Tools import (
    # Arguments
    AlgoliaSearchArguments,
    # Setup
    AlgoliaSetup,
    ArxivSearchArguments,
    BraveSearchArguments,
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
    GoogleSheetsAppendArguments,
    GoogleSheetsBatchReadArguments,
    GoogleSheetsBatchWriteArguments,
    GoogleSheetsClearArguments,
    GoogleSheetsReadArguments,
    GoogleSheetsSetup,
    GoogleSheetsWriteArguments,
    LlamaParseFetchArguments,
    LlamaParseSetup,
    MailgunSendEmailArguments,
    MailgunSetup,
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
from .algolia import AlgoliaSearchOutput
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
from .google_sheets import (
    GoogleSheetsBatchReadOutput,
    GoogleSheetsBatchWriteOutput,
    GoogleSheetsClearOutput,
    GoogleSheetsReadOutput,
    GoogleSheetsValueRangeOutput,
    GoogleSheetsWriteOutput,
)
from .llama_parse import LlamaParseFetchOutput
from .mailgun import MailgunSendEmailOutput
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
    AlgoliaSetup
    | BraveSearchSetup
    | BrowserbaseSetup
    | CloudinarySetup
    | EmailSetup
    | LlamaParseSetup
    | MailgunSetup
    | RemoteBrowserSetup
    | SpiderSetup
    | UnstructuredSetup
    | WeatherSetup
    | GoogleSheetsSetup
)

# Argument configurations
ExecutionArguments = (
    AlgoliaSearchArguments
    | ArxivSearchArguments
    | BraveSearchArguments
    | BrowserbaseCompleteSessionArguments
    | BrowserbaseContextArguments
    | BrowserbaseCreateSessionArguments
    | BrowserbaseExtensionArguments
    | BrowserbaseListSessionsArguments
    | BrowserbaseGetSessionArguments
    | BrowserbaseGetSessionLiveUrlsArguments
    | CloudinaryUploadArguments
    | CloudinaryEditArguments
    | EmailArguments
    | FfmpegSearchArguments
    | LlamaParseFetchArguments
    | MailgunSendEmailArguments
    | RemoteBrowserArguments
    | SpiderFetchArguments
    | UnstructuredPartitionArguments
    | WeatherGetArguments
    | WikipediaSearchArguments
    | GoogleSheetsReadArguments
    | GoogleSheetsWriteArguments
    | GoogleSheetsAppendArguments
    | GoogleSheetsClearArguments
    | GoogleSheetsBatchReadArguments
    | GoogleSheetsBatchWriteArguments
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
    | MailgunSendEmailOutput
    | CloudinaryEditOutput
    | CloudinaryUploadOutput
    | ExecutionError
    | ArxivSearchOutput
    | SpiderOutput
    | UnstructuredParseOutput
    | AlgoliaSearchOutput
    | GoogleSheetsReadOutput
    | GoogleSheetsWriteOutput
    | GoogleSheetsClearOutput
    | GoogleSheetsBatchReadOutput
    | GoogleSheetsBatchWriteOutput
    | GoogleSheetsValueRangeOutput
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
