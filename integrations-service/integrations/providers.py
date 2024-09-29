from .models.base_models import BaseProvider, BaseProviderMethod, ProviderInfo
from .models.wikipedia import WikipediaSearchArguments, WikipediaSearchOutput
from .models.weather import WeatherGetArguments, WeatherGetOutput, WeatherSetup
from .models.hacker_news import HackerNewsFetchArguments, HackerNewsFetchOutput
from .models.spider import SpiderFetchArguments, SpiderFetchOutput, SpiderSetup

wikipedia = BaseProvider(
    provider="wikipedia",
    setup=None,
    methods=[
        BaseProviderMethod(
            method="search",
            description="Search for a page on Wikipedia",
            arguments=WikipediaSearchArguments,
            output=WikipediaSearchOutput,
        ),
    ],
    info=ProviderInfo(
        url="https://www.wikipedia.org/",
        docs="https://www.wikipedia.org/wiki/Main_Page",
        icon="https://www.wikipedia.org/static/favicon/wikipedia.ico",
        friendly_name="Wikipedia",
    ),
)

weather = BaseProvider(
    provider="weather",
    setup=WeatherSetup,
    methods=[
        BaseProviderMethod(
            method="get",
            description="Get the current weather for a city",
            arguments=WeatherGetArguments,
            output=WeatherGetOutput,
        ),
    ],
    info=ProviderInfo(
        url="https://www.weatherapi.com/",
        docs="https://www.weatherapi.com/docs/",
        icon="https://www.weatherapi.com/favicon.ico",
        friendly_name="Weather API",
    ),
)

hacker_news = BaseProvider(
    provider="hacker_news",
    setup=None,
    methods=[
        BaseProviderMethod(
            method="fetch",
            description="Get the top stories from Hacker News",
            arguments=HackerNewsFetchArguments,
            output=HackerNewsFetchOutput,
        ),
    ],
    info=ProviderInfo(
        url="https://news.ycombinator.com/",
        docs="https://news.ycombinator.com/newsguidelines.html",
        icon="https://news.ycombinator.com/favicon.ico",
        friendly_name="Hacker News",
    ),
)

spider = BaseProvider(
    provider="spider",
    setup=SpiderSetup,
    methods=[
        BaseProviderMethod(
            method="crawl",
            description="Crawl a website and extract data",
            arguments=SpiderFetchArguments,
            output=SpiderFetchOutput,
        ),
    ],
    info=ProviderInfo(
        url="https://spider.com/",
        docs="https://spider.com/docs/",
        icon="https://spider.com/favicon.ico",
        friendly_name="Spider",
    ),
)

providers = {
    "wikipedia": wikipedia,
    "weather": weather,
    "hacker_news": hacker_news,
    "spider": spider,
}