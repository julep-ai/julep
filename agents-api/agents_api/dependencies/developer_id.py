import uuid
from typing import Annotated
from fastapi import Header
from pydantic import validate_email
from pydantic_core import PydanticCustomError

from ..env import skip_check_developer_headers
from .exceptions import InvalidHeaderFormat


async def get_developer_id(
    x_developer_id: Annotated[uuid.UUID | None, Header()] = None
):
    if skip_check_developer_headers:
        return x_developer_id or uuid.UUID("00000000-0000-0000-0000-000000000000")

    if not x_developer_id:
        raise InvalidHeaderFormat("X-Developer-Id header invalid")

    if isinstance(x_developer_id, str):
        try:
            x_developer_id = uuid.UUID(x_developer_id, version=4)
        except ValueError:
            raise InvalidHeaderFormat("X-Developer-Id must be a valid UUID")

    return x_developer_id


async def get_developer_email(
    x_developer_email: Annotated[str | None, Header()] = None
):
    if skip_check_developer_headers:
        return x_developer_email or "unknown_user@mail.com"

    if not x_developer_email:
        raise InvalidHeaderFormat("X-Developer-Email header invalid")

    try:
        validate_email(x_developer_email)
    except PydanticCustomError:
        raise InvalidHeaderFormat("X-Developer-Email header invalid")

    return x_developer_email
