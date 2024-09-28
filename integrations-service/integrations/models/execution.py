from typing import Optional, Union

from pydantic import BaseModel

from .hacker_news import HackerNewsArguments, HackerNewsOutput
from .spider import SpiderArguments, SpiderOutput, SpiderSetup
from .weather import WeatherArguments, WeatherOutput, WeatherSetup
from .wikipedia import WikipediaArguments, WikipediaOutput

ExecutionSetup = Union[SpiderSetup, WeatherSetup]
ExecutionArguments = Union[
    SpiderArguments, WeatherArguments, HackerNewsArguments, WikipediaArguments
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


ExecutionResponse = Union[
    SpiderOutput, WeatherOutput, HackerNewsOutput, WikipediaOutput
]
