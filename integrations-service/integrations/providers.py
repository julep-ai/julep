from .autogen.Tools import (
    BraveSearchArguments,
    BraveSearchSetup,
    EmailArguments,
    EmailSetup,
    SpiderFetchArguments,
    SpiderSetup,
    WeatherGetArguments,
    WeatherSetup,
    WikipediaSearchArguments,
    # WikipediaSearchSetup,
)
from .models import (
    BaseProvider,
    BaseProviderMethod,
    BraveSearchOutput,
    EmailOutput,
    ProviderInfo,
    SpiderFetchOutput,
    WeatherGetOutput,
    WikipediaSearchOutput,
)

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

brave = BaseProvider(
    provider="brave",
    setup=BraveSearchSetup,
    methods=[
        BaseProviderMethod(
            method="search",
            description="Search with Brave",
            arguments=BraveSearchArguments,
            output=BraveSearchOutput,
        ),
    ],
    info=ProviderInfo(
        url="https://brave.com/",
        docs="https://brave.com/docs/",
        icon="https://brave.com/favicon.ico",
        friendly_name="Brave Search",
    ),
)

email = BaseProvider(
    provider="email",
    setup=EmailSetup,
    methods=[
        BaseProviderMethod(
            method="send",
            description="Send an email",
            arguments=EmailArguments,
            output=EmailOutput,
        ),
    ],
    info=ProviderInfo(
        friendly_name="Email",
    ),
)

available_providers: dict[str, BaseProvider] = {
    "wikipedia": wikipedia,
    "weather": weather,
    "spider": spider,
    "brave": brave,
    "email": email,
}
