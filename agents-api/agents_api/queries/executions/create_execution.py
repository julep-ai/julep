from typing import Annotated, Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pydantic import ValidationError
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateExecutionRequest, Execution
from ...common.utils.types import dict_like
from ...metrics.counters import increase_counter
from ..utils import (
    partialclass,
    rewrap_exceptions,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


# @rewrap_exceptions(
#     {
#         QueryException: partialclass(HTTPException, status_code=400),
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#     }
# )
# @wrap_in_class(
#     Execution,
#     one=True,
#     transform=lambda d: {"id": d["execution_id"], **d},
#     _kind="inserted",
# )
# @increase_counter("create_execution")
# @beartype
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

    # columns, values = cozo_process_mutate_data(
    #     {
    #         **execution_data,
    #         "task_id": task_id,
    #         "execution_id": execution_id,
    #     }
    # )

    # insert_query = f"""
    # ?[{columns}] <- $values

    # :insert executions {{
    #     {columns}
    # }}

    # :returning
    # """

    # queries = [
    #     verify_developer_id_query(developer_id),
    #     verify_developer_owns_resource_query(
    #         developer_id,
    #         "tasks",
    #         task_id=task_id,
    #         parents=[("agents", "agent_id")],
    #     ),
    #     insert_query,
    # ]

    # return (queries, {"values": values})
