from typing import Annotated
from uuid import UUID

from fastapi import Header

from ..common.protocol.developers import Developer
from ..env import multi_tenant_mode
from ..queries.developers.get_developer import get_developer
from .exceptions import InvalidHeaderFormat


async def get_developer_id(
    x_developer_id: Annotated[UUID | None, Header(include_in_schema=False)] = None,
) -> UUID:
    if not multi_tenant_mode:
        return UUID("00000000-0000-0000-0000-000000000000")

    if not x_developer_id:
        msg = "X-Developer-Id header required"
        raise InvalidHeaderFormat(msg)

    if isinstance(x_developer_id, str):
        try:
            x_developer_id = UUID(x_developer_id, version=4)
        except ValueError as e:
            msg = "X-Developer-Id must be a valid UUID"
            raise InvalidHeaderFormat(msg) from e

    return x_developer_id


async def get_developer_data(
    x_developer_id: Annotated[UUID | None, Header(include_in_schema=False)] = None,
) -> Developer:
    # if not multi_tenant_mode:
    #     # assert not x_developer_id, "X-Developer-Id header not allowed in single-tenant mode"
    #     return await get_developer(developer_id=UUID("00000000-0000-0000-0000-000000000000"))

    if not x_developer_id:
        msg = "X-Developer-Id header required"
        raise InvalidHeaderFormat(msg)

    if isinstance(x_developer_id, str):
        try:
            x_developer_id = UUID(x_developer_id, version=4)
        except ValueError as e:
            msg = "X-Developer-Id must be a valid UUID"
            raise InvalidHeaderFormat(msg) from e

    return await get_developer(developer_id=x_developer_id)
