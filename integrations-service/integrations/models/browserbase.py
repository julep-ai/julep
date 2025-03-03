from typing import Literal

from browserbase.types import Session
from browserbase.types.session_live_urls import SessionLiveURLs
from pydantic import AnyUrl, Field

from .base_models import BaseOutput


class BrowserbaseListSessionsOutput(BaseOutput):
    sessions: list[Session] = Field(..., description="The list of sessions")


class BrowserbaseCreateSessionOutput(BaseOutput):
    id: str = Field(..., description="Unique identifier for the session")
    connect_url: str | None = Field(None, description="The connection URL for the session")
    createdAt: str | None = Field(
        None,
        description="Timestamp indicating when the session was created",
    )
    projectId: str | None = Field(None, description="The Project ID linked to the Session")
    startedAt: str | None = Field(None, description="Timestamp when the session started")
    endedAt: str | None = Field(None, description="Timestamp when the session ended")
    expiresAt: str | None = Field(
        None,
        description="Timestamp when the session is set to expire",
    )
    status: Literal["RUNNING", "ERROR", "TIMED_OUT", "COMPLETED"] | None = Field(
        None,
        description="Current status of the session",
    )
    proxyBytes: int | None = Field(None, description="Bytes used via the Proxy")
    avgCpuUsage: int | None = Field(None, description="CPU used by the Session")
    memoryUsage: int | None = Field(None, description="Memory used by the Session")
    keepAlive: bool | None = Field(
        None,
        description="Indicates if the Session was created to be kept alive upon disconnections",
    )
    contextId: str | None = Field(
        None,
        description="Optional. The Context linked to the Session.",
    )


class BrowserbaseGetSessionOutput(BaseOutput):
    id: str = Field(..., description="Unique identifier for the session")
    createdAt: str | None = Field(
        None,
        description="Timestamp indicating when the session was created",
    )
    projectId: str | None = Field(None, description="The Project ID linked to the Session")
    startedAt: str | None = Field(None, description="Timestamp when the session started")
    endedAt: str | None = Field(None, description="Timestamp when the session ended")
    expiresAt: str | None = Field(
        None,
        description="Timestamp when the session is set to expire",
    )
    status: Literal["RUNNING", "ERROR", "TIMED_OUT", "COMPLETED"] | None = Field(
        None,
        description="Current status of the session",
    )
    proxyBytes: int | None = Field(None, description="Bytes used via the Proxy")
    avgCpuUsage: int | None = Field(None, description="CPU used by the Session")
    memoryUsage: int | None = Field(None, description="Memory used by the Session")
    keepAlive: bool | None = Field(
        None,
        description="Indicates if the Session was created to be kept alive upon disconnections",
    )
    contextId: str | None = Field(
        None,
        description="Optional. The Context linked to the Session.",
    )


class BrowserbaseCompleteSessionOutput(BaseOutput):
    success: bool = Field(
        ...,
        description="Indicates if the session was completed successfully",
    )


class BrowserbaseExtensionOutput(BaseOutput):
    id: str = Field(..., description="Unique identifier for the extension")


class PageInfo(BaseOutput):
    id: str | None = Field(None, description="Unique identifier for the page")
    url: AnyUrl | None = Field(None, description="URL of the page")
    faviconUrl: AnyUrl | None = Field(None, description="URL for the page's favicon")
    title: str | None = Field(None, description="Title of the page")
    debuggerUrl: AnyUrl | None = Field(
        None,
        description="URL to access the debugger for this page",
    )
    debuggerFullscreenUrl: AnyUrl | None = Field(
        None,
        description="URL to access the debugger in fullscreen for this page",
    )


class BrowserbaseGetSessionLiveUrlsOutput(BaseOutput):
    urls: SessionLiveURLs = Field(..., description="The live URLs for the session")


class BrowserbaseContextOutput(BaseOutput):
    id: str = Field(..., description="Unique identifier for the context")
    uploadUrl: str | None = Field(None, description="The upload URL for the context")
    publicKey: str | None = Field(None, description="The public key for the context")
    cipherAlgorithm: str | None = Field(
        None,
        description="The cipher algorithm for the context",
    )
    initializationVectorSize: int | None = Field(
        None,
        description="The size of the initialization vector",
    )
