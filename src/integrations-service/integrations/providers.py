from .autogen.Tools import (
    AlgoliaSearchArguments,
    AlgoliaSetup,
    ArxivSearchArguments,
    BraveSearchArguments,
    BraveSearchSetup,
    BrowserbaseCompleteSessionArguments,
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
from .models import (
    AlgoliaSearchOutput,
    ArxivSearchOutput,
    BaseProvider,
    BaseProviderMethod,
    BraveSearchOutput,
    BrowserbaseCompleteSessionOutput,
    BrowserbaseCreateSessionOutput,
    BrowserbaseExtensionOutput,
    BrowserbaseGetSessionLiveUrlsOutput,
    BrowserbaseGetSessionOutput,
    BrowserbaseListSessionsOutput,
    CloudinaryEditOutput,
    CloudinaryUploadOutput,
    EmailOutput,
    FfmpegSearchOutput,
    LlamaParseFetchOutput,
    MailgunSendEmailOutput,
    ProviderInfo,
    RemoteBrowserOutput,
    SpiderOutput,
    UnstructuredParseOutput,
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
            output=SpiderOutput,
        ),
        BaseProviderMethod(
            method="links",
            description="Extract all links from the webpage",
            arguments=SpiderFetchArguments,
            output=SpiderOutput,
        ),
        BaseProviderMethod(
            method="screenshot",
            description="Take a screenshot of the webpage",
            arguments=SpiderFetchArguments,
            output=SpiderOutput,
        ),
        BaseProviderMethod(
            method="search",
            description="Search content within the webpage",
            arguments=SpiderFetchArguments,
            output=SpiderOutput,
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

llama_parse = BaseProvider(
    provider="llama_parse",
    setup=LlamaParseSetup,
    methods=[
        BaseProviderMethod(
            method="parse",
            description="Parse and extract the files",
            arguments=LlamaParseFetchArguments,
            output=LlamaParseFetchOutput,
        ),
    ],
    info=ProviderInfo(
        friendly_name="LlamaParse",
        url="https://www.llamaindex.ai/",
        docs="https://docs.cloud.llamaindex.ai/llamaparse/getting_started",
        icon="https://www.llamaindex.ai/favicon.ico",
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

ffmpeg = BaseProvider(
    provider="ffmpeg",
    setup=None,
    methods=[
        BaseProviderMethod(
            method="bash_cmd",
            description="Run FFmpeg bash command",
            arguments=FfmpegSearchArguments,
            output=FfmpegSearchOutput,
        ),
    ],
    info=ProviderInfo(
        url="https://ffmpeg.org/",
        docs="https://ffmpeg.org/documentation.html",
        icon="https://upload.wikimedia.org/wikipedia/commons/5/5f/FFmpeg_Logo_new.svg",
        friendly_name="Ffmpeg",
    ),
)

cloudinary = BaseProvider(
    provider="cloudinary",
    setup=CloudinarySetup,
    methods=[
        BaseProviderMethod(
            method="media_edit",
            description="Edit media in Cloudinary",
            arguments=CloudinaryEditArguments,
            output=CloudinaryEditOutput,
        ),
        BaseProviderMethod(
            method="media_upload",
            description="Upload media to Cloudinary",
            arguments=CloudinaryUploadArguments,
            output=CloudinaryUploadOutput,
        ),
    ],
    info=ProviderInfo(
        url="https://cloudinary.com/",
        docs="https://cloudinary.com/documentation/python_quickstart",
        icon="https://cloudinary.com/favicon.ico",
        friendly_name="Cloudinary",
    ),
)

arxiv = BaseProvider(
    provider="arxiv",
    setup=None,
    methods=[
        BaseProviderMethod(
            method="search",
            description="Search in Arxiv",
            arguments=ArxivSearchArguments,
            output=ArxivSearchOutput,
        ),
    ],
    info=ProviderInfo(
        url="https://pypi.org/project/arxiv/",
        docs="https://info.arxiv.org/help/api/index.html",
        icon="https://arxiv.com/favicon.ico",
        friendly_name="Arxiv Search",
    ),
)

unstructured = BaseProvider(
    provider="unstructured",
    setup=UnstructuredSetup,
    methods=[
        BaseProviderMethod(
            method="parse",
            description="Parse documents into structured elements",
            arguments=UnstructuredPartitionArguments,
            output=UnstructuredParseOutput,
        ),
    ],
    info=ProviderInfo(
        url="https://unstructured.io/",
        docs="https://docs.unstructured.io/",
        icon="https://unstructured.io/favicon.ico",
        friendly_name="Unstructured.io",
    ),
)

algolia = BaseProvider(
    provider="algolia",
    setup=AlgoliaSetup,
    methods=[
        BaseProviderMethod(
            method="search",
            description="Search for content in an Algolia index",
            arguments=AlgoliaSearchArguments,
            output=AlgoliaSearchOutput,
        ),
    ],
    info=ProviderInfo(
        url="https://www.algolia.com/",
        docs="https://www.algolia.com/doc/",
        icon="https://www.algolia.com/favicon.ico",
        friendly_name="Algolia Search",
    ),
)

mailgun = BaseProvider(
    provider="mailgun",
    setup=MailgunSetup,
    methods=[
        BaseProviderMethod(
            method="send_email",
            description="Send an email",
            arguments=MailgunSendEmailArguments,
            output=MailgunSendEmailOutput,
        ),
    ],
    info=ProviderInfo(
        friendly_name="Mailgun",
        url="https://www.mailgun.com/",
        docs="https://documentation.mailgun.com/",
        icon="https://www.mailgun.com/favicon.ico",
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
    "llama_parse": llama_parse,
    "ffmpeg": ffmpeg,
    "cloudinary": cloudinary,
    "arxiv": arxiv,
    "unstructured": unstructured,
    "algolia": algolia,
    "mailgun": mailgun,
}
