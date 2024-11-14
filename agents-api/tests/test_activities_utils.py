from datetime import datetime, timezone
from uuid import uuid4

from ward import test

from agents_api.activities.utils import get_integration_arguments
from agents_api.autogen.Tools import (
    BraveIntegrationDef,
    BrowserbaseCompleteSessionIntegrationDef,
    BrowserbaseContextIntegrationDef,
    BrowserbaseCreateSessionIntegrationDef,
    BrowserbaseExtensionIntegrationDef,
    BrowserbaseGetSessionConnectUrlIntegrationDef,
    BrowserbaseGetSessionIntegrationDef,
    BrowserbaseGetSessionLiveUrlsIntegrationDef,
    BrowserbaseListSessionsIntegrationDef,
    DummyIntegrationDef,
    EmailIntegrationDef,
    RemoteBrowserIntegrationDef,
    RemoteBrowserSetup,
    SpiderIntegrationDef,
    Tool,
    WeatherIntegrationDef,
    WikipediaIntegrationDef,
)


@test("get_integration_arguments: dummy search")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=DummyIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {},
        "required": [],
    }


@test("get_integration_arguments: brave search")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=BraveIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query for searching with Brave",
            }
        },
        "required": ["query"],
    }


@test("get_integration_arguments: email search")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=EmailIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "The email address to send the email to",
            },
            "from_": {
                "type": "string",
                "description": "The email address to send the email from",
            },
            "subject": {
                "type": "string",
                "description": "The subject of the email",
            },
            "body": {
                "type": "string",
                "description": "The body of the email",
            },
        },
        "required": ["to", "from_", "subject", "body"],
    }


@test("get_integration_arguments: spider fetch")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=SpiderIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "url": {
                "type": "object",
                "description": "The URL to fetch data from",
            },
            "mode": {
                "type": "string",
                "description": "The type of crawler to use",
                "enum": "scrape",
            },
            "params": {
                "type": "object",
                "description": "Additional parameters for the Spider API",
            },
        },
        "required": ["url"],
    }


@test("get_integration_arguments: wikipedia integration")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=WikipediaIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string",
            },
            "load_max_docs": {
                "type": "number",
                "description": "Maximum number of documents to load",
            },
        },
        "required": ["query"],
    }


@test("get_integration_arguments: weather integration")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=WeatherIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location for which to fetch weather data",
            }
        },
        "required": ["location"],
    }


@test("get_integration_arguments: browserbase context")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=BrowserbaseContextIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "The Project ID. Can be found in Settings.",
            },
        },
        "required": ["project_id"],
    }


@test("get_integration_arguments: browserbase extension")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=BrowserbaseExtensionIntegrationDef(
            method="install_extension_from_github"
        ),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "repository_name": {
                "type": "string",
                "description": "The GitHub repository name.",
            },
            "ref": {
                "type": "string",
                "description": "Ref to install from a branch or tag.",
            },
        },
        "required": ["repository_name"],
    }


@test("get_integration_arguments: browserbase list sessions")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=BrowserbaseListSessionsIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "The status of the sessions to list (Available options: RUNNING, ERROR, TIMED_OUT, COMPLETED)",
                "enum": "RUNNING,ERROR,TIMED_OUT,COMPLETED",
            }
        },
        "required": [],
    }


@test("get_integration_arguments: browserbase create session")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=BrowserbaseCreateSessionIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "The Project ID. Can be found in Settings.",
            },
            "extension_id": {
                "type": "string",
                "description": "The installed Extension ID. See Install Extension from GitHub.",
            },
            "browser_settings": {
                "type": "object",
                "description": "Browser settings",
            },
            "timeout": {
                "type": "number",
                "description": "Duration in seconds after which the session will automatically end. Defaults to the Project's defaultTimeout.",
            },
            "keep_alive": {
                "type": "boolean",
                "description": "Set to true to keep the session alive even after disconnections. This is available on the Startup plan only.",
            },
            "proxies": {
                "type": "boolean | array",
                "description": "Proxy configuration. Can be true for default proxy, or an array of proxy configurations.",
            },
        },
        "required": [],
    }


@test("get_integration_arguments: browserbase get session")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=BrowserbaseGetSessionIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Session ID",
            },
        },
        "required": ["id"],
    }


@test("get_integration_arguments: browserbase complete session")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=BrowserbaseCompleteSessionIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Session ID",
            },
            "status": {
                "type": "string",
                "description": "Session status",
                "enum": "REQUEST_RELEASE",
            },
        },
        "required": ["id"],
    }


@test("get_integration_arguments: browserbase get session live urls")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=BrowserbaseGetSessionLiveUrlsIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Session ID",
            },
        },
        "required": ["id"],
    }


@test("get_integration_arguments: browserbase get session connect url")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=BrowserbaseGetSessionConnectUrlIntegrationDef(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Session ID",
            },
        },
        "required": ["id"],
    }


@test("get_integration_arguments: remote browser")
async def _():
    tool = Tool(
        id=uuid4(),
        name="tool1",
        type="integration",
        integration=RemoteBrowserIntegrationDef(setup=RemoteBrowserSetup()),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = get_integration_arguments(tool)

    assert result == {
        "type": "object",
        "properties": {
            "connect_url": {
                "type": "string",
                "description": "The connection URL for the remote browser",
            },
            "action": {
                "type": "string",
                "description": "The action to perform",
                "enum": "key,type,mouse_move,left_click,left_click_drag,right_click,middle_click,double_click,screenshot,cursor_position,navigate,refresh",
            },
            "text": {
                "type": "string",
                "description": "The text",
            },
            "coordinate": {
                "type": "array",
                "description": "The coordinate to move the mouse to",
            },
        },
        "required": ["action"],
    }
