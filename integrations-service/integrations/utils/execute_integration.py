from ..models.base_models import IdentifierName
from ..models.execution import ExecutionArguments, ExecutionResponse, ExecutionSetup
from ..models.hacker_news import HackerNewsArguments
from ..models.spider import SpiderArguments, SpiderSetup
from ..models.weather import WeatherArguments, WeatherSetup
from ..models.wikipedia import WikipediaArguments
from .integrations.hacker_news import hacker_news
from .integrations.spider import spider
from .integrations.weather import weather
from .integrations.wikipedia import wikipedia


async def execute_integration(
    provider: IdentifierName,
    arguments: ExecutionArguments,
    method: IdentifierName | None = None,
    setup: ExecutionSetup | None = None,
) -> ExecutionResponse:
    match provider:
        case "wikipedia":
            return await wikipedia(
                arguments=WikipediaArguments(**arguments.model_dump())
            )
        case "weather":
            return await weather(
                setup=WeatherSetup(**setup.model_dump()),
                arguments=WeatherArguments(**arguments.model_dump()),
            )
        case "hacker_news":
            return await hacker_news(
                arguments=HackerNewsArguments(**arguments.model_dump())
            )
        case "spider":
            return await spider(
                setup=SpiderSetup(**setup.model_dump()),
                arguments=SpiderArguments(**arguments.model_dump()),
            )
        case _:
            raise ValueError(f"Unknown integration: {provider}")
