from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from jsonschema import validate
from jsonschema.exceptions import SchemaError, ValidationError
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from ...autogen.openapi_model import CreateTaskRequest, Task
from ...common.utils.task_validation import validate_task
from ...common.utils.tool_validation import validate_tool
from ...dependencies.developer_id import get_developer_id
from ...queries.tasks.create_task import create_task as create_task_query
from .router import router


@router.post("/agents/{agent_id}/tasks", status_code=HTTP_201_CREATED, tags=["tasks"])
async def create_task(
    data: CreateTaskRequest,
    agent_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> Task:
    # Validate the input schema
    try:
        if data.input_schema is not None:
            validate(None, data.input_schema)
    except SchemaError:
        raise HTTPException(detail="Invalid input schema", status_code=HTTP_400_BAD_REQUEST)
    except ValidationError:
        pass

    # Validate Python expressions in the task spec
    for tool in data.tools:
        await validate_tool(tool)

    validation_result = validate_task(data)
    if not validation_result.is_valid:
        # Prepare a detailed error response

        # Gather all issues categorized by type
        issues = [
            {
                "location": issue.location,
                "message": issue.message,
                "severity": issue.severity,
                "type": "python_expression",
                **({} if issue.details is None else {"details": issue.details}),
            }
            for issue in validation_result.python_expression_issues
        ]

        issues.extend(
            {
                "location": issue.location,
                "message": issue.message,
                "severity": issue.severity,
                "type": "schema",
            }
            for issue in validation_result.schema_issues
        )

        issues.extend(
            {
                "location": issue.location,
                "message": issue.message,
                "severity": issue.severity,
                "type": "other",
            }
            for issue in validation_result.other_issues
        )

        # Return a structured error response
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail={
                "message": "Task specification contains validation errors",
                "issues": issues,
            },
        )

    return await create_task_query(
        developer_id=x_developer_id,
        agent_id=agent_id,
        data=data,
    )
