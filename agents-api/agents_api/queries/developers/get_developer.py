"""
Module for retrieving developer information from the PostgreSQL database.
"""

from uuid import UUID

from beartype import beartype

from ...common.protocol.developers import Developer
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

developer_query = """
SELECT * FROM developers WHERE developer_id = $1 -- developer_id
"""


@rewrap_exceptions(common_db_exceptions("developer", ["get"]))
@wrap_in_class(
    Developer,
    one=True,
    transform=lambda d: {**d, "id": d["developer_id"]},
)
@pg_query
@beartype
async def get_developer(
    *,
    developer_id: UUID,
) -> tuple[str, list]:
    developer_id = str(developer_id)

    return (
        developer_query,
        [developer_id],
    )
