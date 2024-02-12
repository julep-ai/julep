import uuid
from typing import Annotated
from fastapi import Header
from pydantic import validate_email
from pydantic_core import PydanticCustomError
from ..env import skip_check_developer_headers
from .exceptions import InvalidHeaderFormat


async def get_developer_id(x_developer_id: Annotated[str | None, Header()] = None):
    if x_developer_id is None:
        if not skip_check_developer_headers:
            raise InvalidHeaderFormat("X-Developer-Id header invalid")
        else:
            x_developer_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

    if isinstance(x_developer_id, str):
        try:
            x_developer_id = uuid.UUID(x_developer_id, version=4)
        except ValueError:
            raise InvalidHeaderFormat("X-Developer-Id must be a valid UUID")

    return x_developer_id


async def get_developer_email(
    x_developer_email: Annotated[str | None, Header()] = None
):
    if x_developer_email is None:
        if not skip_check_developer_headers:
            raise InvalidHeaderFormat("X-Developer-Email header invalid")
        else:
            x_developer_email = "unknown_user@mail.com"

    try:
        validate_email(x_developer_email)
    except PydanticCustomError:
        raise InvalidHeaderFormat("X-Developer-Email header invalid")

    return x_developer_email
