import asyncio
import contextlib
import os
import tempfile

import httpx
from beartype import beartype
from browserbase import Browserbase
from browserbase.types.session import Session
from browserbase.types.session_create_params import BrowserSettings
from browserbase.types.session_live_urls import SessionLiveURLs
from pydantic import TypeAdapter
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import (
    BrowserbaseCompleteSessionArguments,
    BrowserbaseCreateSessionArguments,
    BrowserbaseExtensionArguments,
    BrowserbaseGetSessionArguments,
    BrowserbaseGetSessionLiveUrlsArguments,
    BrowserbaseListSessionsArguments,
    BrowserbaseSetup,
)
from ...env import (
    browserbase_api_key,
    browserbase_project_id,
)
from ...models import (
    BrowserbaseCompleteSessionOutput,
    BrowserbaseCreateSessionOutput,
    BrowserbaseGetSessionLiveUrlsOutput,
    BrowserbaseGetSessionOutput,
    BrowserbaseListSessionsOutput,
)
from ...models.browserbase import BrowserbaseExtensionOutput


def get_browserbase_client(setup: BrowserbaseSetup) -> Browserbase:
    setup.api_key = browserbase_api_key if setup.api_key == "DEMO_API_KEY" else setup.api_key
    setup.project_id = (
        browserbase_project_id if setup.project_id == "DEMO_PROJECT_ID" else setup.project_id
    )

    return Browserbase(
        api_key=setup.api_key,
    )


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def list_sessions(
    setup: BrowserbaseSetup,
    arguments: BrowserbaseListSessionsArguments,
) -> BrowserbaseListSessionsOutput:
    client = get_browserbase_client(setup)

    try:
        # Add status filter if provided
        params = {}
        if hasattr(arguments, "status") and arguments.status:
            params["status"] = arguments.status

        sessions: list[Session] = client.sessions.list(**params)
        return BrowserbaseListSessionsOutput(sessions=sessions)
    except Exception as e:
        print(f"Error listing sessions: {e}")
        raise


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def create_session(
    setup: BrowserbaseSetup,
    arguments: BrowserbaseCreateSessionArguments,
) -> BrowserbaseCreateSessionOutput:
    client = get_browserbase_client(setup)

    if arguments.project_id == "DEMO_PROJECT_ID":
        arguments.project_id = browserbase_project_id

    # Convert browser settings using TypeAdapter
    browser_settings = TypeAdapter(BrowserSettings).validate_python(arguments.browser_settings)

    # Create session parameters
    create_params = {
        "project_id": arguments.project_id or setup.project_id,
        "browser_settings": browser_settings,
    }

    # Only add extension_id if it's provided and not None/empty
    if arguments.extension_id:
        create_params["extension_id"] = arguments.extension_id

    # Changed to use sessions.create() with direct parameters
    session = client.sessions.create(**create_params)

    # Convert datetime fields to ISO format strings
    return BrowserbaseCreateSessionOutput(
        id=session.id,
        connect_url=session.connect_url,
        createdAt=session.created_at.isoformat() if session.created_at else None,
        projectId=session.project_id,
        startedAt=session.started_at.isoformat() if session.started_at else None,
        endedAt=session.ended_at.isoformat() if session.ended_at else None,
        expiresAt=session.expires_at.isoformat() if session.expires_at else None,
        status=session.status,
        proxyBytes=session.proxy_bytes,
        avgCpuUsage=session.avg_cpu_usage,
        memoryUsage=session.memory_usage,
        keepAlive=session.keep_alive,
        contextId=session.context_id,
    )


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def get_session(
    setup: BrowserbaseSetup,
    arguments: BrowserbaseGetSessionArguments,
) -> BrowserbaseGetSessionOutput:
    client = get_browserbase_client(setup)

    # Changed from get_session() to sessions.retrieve()
    session = client.sessions.retrieve(id=arguments.id)

    return BrowserbaseGetSessionOutput(
        id=session.id,
        createdAt=session.created_at.isoformat() if session.created_at else None,
        projectId=session.project_id,
        startedAt=session.started_at.isoformat() if session.started_at else None,
        endedAt=session.ended_at.isoformat() if session.ended_at else None,
        expiresAt=session.expires_at.isoformat() if session.expires_at else None,
        status=session.status,
        proxyBytes=session.proxy_bytes,
        avgCpuUsage=session.avg_cpu_usage,
        memoryUsage=session.memory_usage,
        keepAlive=session.keep_alive,
        contextId=session.context_id,
    )


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def complete_session(
    setup: BrowserbaseSetup,
    arguments: BrowserbaseCompleteSessionArguments,
) -> BrowserbaseCompleteSessionOutput:
    client = get_browserbase_client(setup)

    try:
        # Changed to use sessions.update() with REQUEST_RELEASE status
        client.sessions.update(
            id=arguments.id,
            status="REQUEST_RELEASE",
            project_id=setup.project_id,
        )
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
    setup: BrowserbaseSetup,
    arguments: BrowserbaseGetSessionLiveUrlsArguments,
) -> BrowserbaseGetSessionLiveUrlsOutput:
    """Get the live URLs for a session."""
    client = get_browserbase_client(setup)
    try:
        # Use the debug() method to get live URLs
        urls: SessionLiveURLs = await asyncio.to_thread(client.sessions.debug, id=arguments.id)
        return BrowserbaseGetSessionLiveUrlsOutput(urls=urls)
    except Exception as e:
        print(f"Error getting debug URLs: {e}")
        raise


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def install_extension_from_github(
    setup: BrowserbaseSetup,
    arguments: BrowserbaseExtensionArguments,
) -> BrowserbaseExtensionOutput:
    """Download and install an extension from GitHub to the user's Browserbase account."""
    try:
        github_url = f"https://github.com/{arguments.repository_name}/archive/refs/tags/{arguments.ref}.zip"

        async with httpx.AsyncClient(timeout=600) as client:
            # Download the extension zip
            try:
                response = await client.get(github_url, follow_redirects=True)
                response.raise_for_status()
            except httpx.HTTPError as e:
                print(f"Error downloading extension from GitHub: {e}")
                raise

            with tempfile.NamedTemporaryFile(
                delete=True,
                delete_on_close=False,
                suffix=".zip",
            ) as tmp_file:
                tmp_file.write(response.content)
                tmp_file_path = tmp_file.name

                upload_url = "https://api.browserbase.com/v1/extensions"
                headers = {
                    "X-BB-API-Key": setup.api_key,
                }

                try:
                    with open(tmp_file_path, "rb") as f:
                        files = {"file": f}
                        upload_response = await client.post(
                            upload_url,
                            headers=headers,
                            files=files,
                        )
                        upload_response.raise_for_status()
                except httpx.HTTPError as e:
                    print(f"Error uploading extension to Browserbase: {e}")
                    if hasattr(e, "response") and e.response is not None:
                        print(f"Response content: {e.response.text}")
                    raise

                # Delete the temporary file
                with contextlib.suppress(FileNotFoundError):
                    os.remove(tmp_file_path)

                return BrowserbaseExtensionOutput(id=upload_response.json()["id"])
    except Exception as e:
        print(f"Unexpected error in install_extension_from_github: {e}")
        raise
