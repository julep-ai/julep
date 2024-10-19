from .models import (
    BaseProvider,
    BaseProviderMethod,
    BraveSearchArguments,
    BraveSearchOutput,
    BraveSearchSetup,
    BrowserBaseLoadArguments,
    BrowserBaseLoadOutput,
    BrowserBaseSetup,
    EmailArguments,
    EmailOutput,
    EmailSetup,
    ProviderInfo,
    SpiderFetchArguments,
    SpiderFetchOutput,
    SpiderSetup,
    WeatherGetArguments,
    WeatherGetOutput,
    WeatherSetup,
    WikipediaSearchArguments,
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

browserbase = BaseProvider(
    provider="browserbase",
    setup=BrowserBaseSetup,
    methods=[
        BaseProviderMethod(
            method="load",
            description="Load documents from the provided urls",
            arguments=BrowserBaseLoadArguments,
            output=BrowserBaseLoadOutput,
        ),
    ],
    info=ProviderInfo(
        url="https://browserbase.com/",
        docs="https://browserbase.com/docs/",
        icon="https://browserbase.com/favicon.ico",
        friendly_name="BrowserBase",
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

providers = {
    "wikipedia": wikipedia,
    "weather": weather,
    "spider": spider,
    "brave": brave,
    "browserbase": browserbase,
    "email": email,
}
