from typing import Annotated, Any, TypeVar
from uuid import UUID

from beartype import beartype
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateExecutionRequest, Execution
from ...common.utils.types import dict_like
from ...metrics.counters import increase_counter
from ..utils import (
    pg_query,
    wrap_in_class,
)
from .constants import OUTPUT_UNNEST_KEY

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

sql_query = """
INSERT INTO executions
(
    developer_id,
    task_id,
    execution_id,
    input,
    metadata,
)
VALUES
(
    $1,
    $2,
    $3,
    $4,
    $5
)
RETURNING *;
"""


# @rewrap_exceptions(
#     {
#         QueryException: partialclass(HTTPException, status_code=400),
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#     }
# )
@wrap_in_class(
    Execution,
    one=True,
    transform=lambda d: {"id": d["execution_id"], **d},
)
@pg_query
@increase_counter("create_execution")
@beartype
async def create_execution(
    *,
    developer_id: UUID,
    task_id: UUID,
    execution_id: UUID | None = None,
    data: Annotated[CreateExecutionRequest | dict, dict_like(CreateExecutionRequest)],
) -> tuple[list[str], dict]:
    execution_id = execution_id or uuid7()

    # developer_id = str(developer_id)
    # task_id = str(task_id)
    # execution_id = str(execution_id)

    # if isinstance(data, CreateExecutionRequest):
    #     data.metadata = data.metadata or {}
    #     execution_data = data.model_dump()
    # else:
    #     data["metadata"] = data.get("metadata", {})
    #     execution_data = data

    # if execution_data["output"] is not None and not isinstance(
    #     execution_data["output"], dict
    # ):
    #     execution_data["output"] = {OUTPUT_UNNEST_KEY: execution_data["output"]}

    return (
        sql_query,
        [
            developer_id,
            task_id,
            execution_id,
            data["input"],
            data["metadata"],
        ],
    )
