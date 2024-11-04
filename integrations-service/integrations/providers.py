from .autogen.Tools import (
    BraveSearchArguments,
    BraveSearchSetup,
    BrowserbaseCompleteSessionArguments,
    BrowserbaseCreateSessionArguments,
    BrowserbaseExtensionArguments,
    BrowserbaseGetSessionArguments,
    BrowserbaseGetSessionConnectUrlArguments,
    BrowserbaseGetSessionLiveUrlsArguments,
    # WikipediaSearchSetup,
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
from .models import (
    BaseProvider,
    BaseProviderMethod,
    BraveSearchOutput,
    BrowserbaseCompleteSessionOutput,
    BrowserbaseCreateSessionOutput,
    BrowserbaseExtensionOutput,
    BrowserbaseGetSessionConnectUrlOutput,
    BrowserbaseGetSessionLiveUrlsOutput,
    BrowserbaseGetSessionOutput,
    BrowserbaseListSessionsOutput,
    EmailOutput,
    ProviderInfo,
    RemoteBrowserOutput,
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

browserbase = BaseProvider(
    provider="browserbase",
    setup=BrowserbaseSetup,
    methods=[
        BaseProviderMethod(
            method="list_sessions",
            description="List sessions in Browserbase",
            arguments=BrowserbaseListSessionsArguments,
            output=BrowserbaseListSessionsOutput,
        ),
        BaseProviderMethod(
            method="create_session",
            description="Create a session in Browserbase",
            arguments=BrowserbaseCreateSessionArguments,
            output=BrowserbaseCreateSessionOutput,
        ),
        BaseProviderMethod(
            method="get_session",
            description="Get a session in Browserbase",
            arguments=BrowserbaseGetSessionArguments,
            output=BrowserbaseGetSessionOutput,
        ),
        BaseProviderMethod(
            method="complete_session",
            description="Complete a session in Browserbase",
            arguments=BrowserbaseCompleteSessionArguments,
            output=BrowserbaseCompleteSessionOutput,
        ),
        BaseProviderMethod(
            method="get_live_urls",
            description="Get sessions' live urls in Browserbase",
            arguments=BrowserbaseGetSessionLiveUrlsArguments,
            output=BrowserbaseGetSessionLiveUrlsOutput,
        ),
        BaseProviderMethod(
            method="install_extension_from_github",
            description="Install an extension from GitHub to the browserbase context",
            arguments=BrowserbaseExtensionArguments,
            output=BrowserbaseExtensionOutput,
        ),
        BaseProviderMethod(
            method="get_connect_url",
            description="Get the connection URL for a session",
            arguments=BrowserbaseGetSessionConnectUrlArguments,
            output=BrowserbaseGetSessionConnectUrlOutput,
        ),
    ],
    info=ProviderInfo(
        friendly_name="BrowserBase",
        url="https://browserbase.com/",
        docs="https://browserbase.com/docs/",
        icon="https://browserbase.com/favicon.ico",
    ),
)

remote_browser = BaseProvider(
    provider="remote_browser",
    setup=RemoteBrowserSetup,
    methods=[
        BaseProviderMethod(
            method="perform_action",
            description="Perform an action in the browser",
            arguments=RemoteBrowserArguments,
            output=RemoteBrowserOutput,
        ),
    ],
    info=ProviderInfo(
        friendly_name="Remote Browser",
        url="https://playwright.dev/",
        docs="https://playwright.dev/docs/",
        icon="https://playwright.dev/favicon.ico",
    ),
)

available_providers: dict[str, BaseProvider] = {
    "wikipedia": wikipedia,
    "weather": weather,
    "spider": spider,
    "brave": brave,
    "email": email,
    "browserbase": browserbase,
    "remote_browser": remote_browser,
}
