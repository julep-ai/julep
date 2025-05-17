from __future__ import annotations

# pyright: reportCallIssue=false
from typing import Annotated, Any, Literal

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, StrictBool

# AIDEV-NOTE: These models duplicate a subset of API definitions for CLI usage.


class SecretRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)  # pyright: ignore[call-issue]
    name: str


class FunctionDef(BaseModel):
    """Function tool definition used in CLI models."""

    model_config = ConfigDict(populate_by_name=True)  # pyright: ignore[call-issue]
    name: Any | None = None
    description: Any | None = None
    parameters: dict[str, Any] | None = None


class ApiCallDef(BaseModel):
    """HTTP API call definition."""

    model_config = ConfigDict(populate_by_name=True)  # pyright: ignore[call-issue]

    method: Literal[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
        "HEAD",
        "OPTIONS",
        "CONNECT",
        "TRACE",
    ]
    url: AnyUrl
    schema_: Annotated[dict[str, Any] | None, Field(alias="schema")] = None
    headers: dict[str, str] | None = None
    secrets: dict[str, SecretRef] | None = None
    content: str | None = None
    data: dict[str, Any] | None = None
    files: dict[str, Any] | None = None
    json_: Annotated[dict[str, Any] | None, Field(alias="json")] = None
    cookies: dict[str, str] | None = None
    params: str | dict[str, Any] | None = None
    follow_redirects: StrictBool | None = None
    timeout: int | None = None
    include_response_content: StrictBool = True


class Computer20241022Def(BaseModel):
    """Anthropic computer tool definition."""

    model_config = ConfigDict(populate_by_name=True)  # pyright: ignore[call-issue]
    type: Literal["computer_20241022"] = "computer_20241022"
    name: str = "computer"
    display_width_px: Annotated[int, Field(ge=600)] = 1024
    display_height_px: Annotated[int, Field(ge=400)] = 768
    display_number: Annotated[int, Field(ge=1, le=10)] = 1


class TextEditor20241022Def(BaseModel):
    """Anthropic text editor tool definition."""

    model_config = ConfigDict(populate_by_name=True)  # pyright: ignore[call-issue]
    type: Literal["text_editor_20241022"] = "text_editor_20241022"
    name: str = "str_replace_editor"


class Bash20241022Def(BaseModel):
    """Anthropic bash tool definition."""

    model_config = ConfigDict(populate_by_name=True)  # pyright: ignore[call-issue]
    type: Literal["bash_20241022"] = "bash_20241022"
    name: str = "bash"
