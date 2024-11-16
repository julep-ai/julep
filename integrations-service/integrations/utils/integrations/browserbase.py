import os
import tempfile

import httpx
from beartype import beartype
from browserbase import (
    Browserbase,
    BrowserSettings,
    CreateSessionOptions,
    DebugConnectionURLs,
    Session,
)
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import (
    BrowserbaseCompleteSessionArguments,
    BrowserbaseCreateSessionArguments,
    BrowserbaseExtensionArguments,
    BrowserbaseGetSessionArguments,
    BrowserbaseGetSessionConnectUrlArguments,
    BrowserbaseGetSessionLiveUrlsArguments,
    BrowserbaseListSessionsArguments,
    BrowserbaseSetup,
)
from ...models import (
    BrowserbaseCompleteSessionOutput,
    BrowserbaseCreateSessionOutput,
    BrowserbaseGetSessionConnectUrlOutput,
    BrowserbaseGetSessionLiveUrlsOutput,
    BrowserbaseGetSessionOutput,
    BrowserbaseListSessionsOutput,
)
from ...models.browserbase import BrowserbaseExtensionOutput


def get_browserbase_client(setup: BrowserbaseSetup) -> Browserbase:
    return Browserbase(
        api_key=setup.api_key,
        project_id=setup.project_id,
        api_url=setup.api_url,
        connect_url=setup.connect_url,
    )


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def list_sessions(
    setup: BrowserbaseSetup, arguments: BrowserbaseListSessionsArguments
) -> BrowserbaseListSessionsOutput:
    client = get_browserbase_client(setup)

    # FIXME: Implement status filter
    # Run the list_sessions method
    sessions: list[Session] = client.list_sessions()

    return BrowserbaseListSessionsOutput(sessions=sessions)


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def create_session(
    setup: BrowserbaseSetup, arguments: BrowserbaseCreateSessionArguments
) -> BrowserbaseCreateSessionOutput:
    client = get_browserbase_client(setup)

    options = CreateSessionOptions(
        projectId=arguments.project_id or setup.project_id,
        extensionId=arguments.extension_id,
        browserSettings=BrowserSettings(**arguments.browser_settings),
    )

    session = client.create_session(options)

    return BrowserbaseCreateSessionOutput(**session.model_dump())


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def get_session(
    setup: BrowserbaseSetup, arguments: BrowserbaseGetSessionArguments
) -> BrowserbaseGetSessionOutput:
    client = get_browserbase_client(setup)

    session = client.get_session(arguments.id)

    return BrowserbaseGetSessionOutput(**session.model_dump())


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def complete_session(
    setup: BrowserbaseSetup, arguments: BrowserbaseCompleteSessionArguments
) -> BrowserbaseCompleteSessionOutput:
    client = get_browserbase_client(setup)

    try:
        client.complete_session(arguments.id)
    except Exception:
        return BrowserbaseCompleteSessionOutput(success=False)

    return BrowserbaseCompleteSessionOutput(success=True)


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def get_live_urls(
    setup: BrowserbaseSetup, arguments: BrowserbaseGetSessionLiveUrlsArguments
) -> BrowserbaseGetSessionLiveUrlsOutput:
    """Get the live URLs for a session."""
    client = get_browserbase_client(setup)
    urls: DebugConnectionURLs = client.get_debug_connection_urls(arguments.id)
    return BrowserbaseGetSessionLiveUrlsOutput(urls=urls)


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def get_connect_url(
    setup: BrowserbaseSetup, arguments: BrowserbaseGetSessionConnectUrlArguments
) -> BrowserbaseGetSessionConnectUrlOutput:
    client = get_browserbase_client(setup)

    url = client.get_connect_url(arguments.id)

    return BrowserbaseGetSessionConnectUrlOutput(url=url)


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def install_extension_from_github(
    setup: BrowserbaseSetup, arguments: BrowserbaseExtensionArguments
) -> BrowserbaseExtensionOutput:
    """Download and install an extension from GitHub to the user's Browserbase account."""

    github_url = f"https://github.com/{arguments.repository_name}/archive/refs/tags/{
            arguments.ref}.zip"

    async with httpx.AsyncClient() as client:
        # Download the extension zip
        response = await client.get(github_url, follow_redirects=True)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(
            delete=True, delete_on_close=False, suffix=".zip"
        ) as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name

            # Upload the extension to Browserbase
            upload_url = "https://www.browserbase.com/v1/extensions"
            headers = {
                # NOTE: httpx won't add a boundary if Content-Type header is set when you pass files=
                # "Content-Type": "multipart/form-data",
                "X-BB-API-Key": setup.api_key,
            }

            with open(tmp_file_path, "rb") as f:
                files = {"file": f}
                upload_response = await client.post(
                    upload_url, headers=headers, files=files
                )

            try:
                upload_response.raise_for_status()
            except httpx.HTTPStatusError:
                print(upload_response.text)
                raise

        # Delete the temporary file
        try:
            os.remove(tmp_file_path)
        except FileNotFoundError:
            pass

        return BrowserbaseExtensionOutput(id=upload_response.json()["id"])
