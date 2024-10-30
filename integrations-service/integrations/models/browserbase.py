from typing import Literal, Optional

from pydantic import AnyUrl, Field

from .base_models import BaseOutput


class SessionInfo(BaseOutput):
    id: str = Field(..., description="Unique identifier for the session")
    createdAt: str = Field(
        ..., description="Timestamp indicating when the session was created"
    )
    projectId: str = Field(..., description="The Project ID linked to the Session")
    startedAt: str = Field(..., description="Timestamp when the session started")
    endedAt: str = Field(..., description="Timestamp when the session ended")
    expiresAt: str = Field(
        ..., description="Timestamp when the session is set to expire"
    )
    status: Literal["RUNNING", "ERROR", "TIMED_OUT", "COMPLETED"] = Field(
        ..., description="Current status of the session"
    )
    proxyBytes: int = Field(..., description="Bytes used via the Proxy")
    avgCpuUsage: int = Field(..., description="CPU used by the Session")
    memoryUsage: int = Field(..., description="Memory used by the Session")
    keepAlive: bool = Field(
        ...,
        description="Indicates if the Session was created to be kept alive upon disconnections",
    )
    contextId: Optional[str] = Field(
        None, description="Optional. The Context linked to the Session."
    )


class BrowserbaseListSessionsOutput(BaseOutput):
    sessions: list[SessionInfo] = Field(..., description="The list of sessions")


class BrowserbaseCreateSessionOutput(BaseOutput):
    id: str = Field(..., description="Unique identifier for the session")
    createdAt: str = Field(
        ..., description="Timestamp indicating when the session was created"
    )
    projectId: str = Field(..., description="The Project ID linked to the Session")
    startedAt: str = Field(..., description="Timestamp when the session started")
    endedAt: str = Field(..., description="Timestamp when the session ended")
    expiresAt: str = Field(
        ..., description="Timestamp when the session is set to expire"
    )
    status: Literal["RUNNING", "ERROR", "TIMED_OUT", "COMPLETED"] = Field(
        ..., description="Current status of the session"
    )
    proxyBytes: int = Field(..., description="Bytes used via the Proxy")
    avgCpuUsage: int = Field(..., description="CPU used by the Session")
    memoryUsage: int = Field(..., description="Memory used by the Session")
    keepAlive: bool = Field(
        ...,
        description="Indicates if the Session was created to be kept alive upon disconnections",
    )
    contextId: Optional[str] = Field(
        None, description="Optional. The Context linked to the Session."
    )


class BrowserbaseGetSessionOutput(BaseOutput):
    id: str = Field(..., description="Unique identifier for the session")
    createdAt: str = Field(
        ..., description="Timestamp indicating when the session was created"
    )
    projectId: str = Field(..., description="The Project ID linked to the Session")
    startedAt: str = Field(..., description="Timestamp when the session started")
    endedAt: str = Field(..., description="Timestamp when the session ended")
    expiresAt: str = Field(
        ..., description="Timestamp when the session is set to expire"
    )
    status: Literal["RUNNING", "ERROR", "TIMED_OUT", "COMPLETED"] = Field(
        ..., description="Current status of the session"
    )
    proxyBytes: int = Field(..., description="Bytes used via the Proxy")
    avgCpuUsage: int = Field(..., description="CPU used by the Session")
    memoryUsage: int = Field(..., description="Memory used by the Session")
    keepAlive: bool = Field(
        ...,
        description="Indicates if the Session was created to be kept alive upon disconnections",
    )
    contextId: Optional[str] = Field(
        None, description="Optional. The Context linked to the Session."
    )


class BrowserbaseCompleteSessionOutput(BaseOutput):
    success: bool = Field(
        ..., description="Indicates if the session was completed successfully"
    )


class BrowserbaseExtensionOutput(BaseOutput):
    id: str = Field(..., description="Unique identifier for the extension")


class BrowserbaseGetSessionConnectUrlOutput(BaseOutput):
    url: AnyUrl = Field(..., description="The connection URL for the session")


class PageInfo(BaseOutput):
    id: Optional[str] = Field(None, description="Unique identifier for the page")
    url: Optional[AnyUrl] = Field(None, description="URL of the page")
    faviconUrl: Optional[AnyUrl] = Field(None, description="URL for the page's favicon")
    title: Optional[str] = Field(None, description="Title of the page")
    debuggerUrl: Optional[AnyUrl] = Field(
        None, description="URL to access the debugger for this page"
    )
    debuggerFullscreenUrl: Optional[AnyUrl] = Field(
        None, description="URL to access the debugger in fullscreen for this page"
    )


class BrowserbaseGetSessionLiveUrlsOutput(BaseOutput):
    debuggerFullscreenUrl: Optional[AnyUrl] = Field(
        None, description="Fullscreen debugger URL for the session"
    )
    debuggerUrl: Optional[AnyUrl] = Field(
        None, description="Debugger URL for the session"
    )
    wsUrl: Optional[AnyUrl] = Field(
        None, description="WebSocket URL for live interaction with the session"
    )
    pages: list[PageInfo] = Field(
        ..., description="List of pages associated with the session"
    )
