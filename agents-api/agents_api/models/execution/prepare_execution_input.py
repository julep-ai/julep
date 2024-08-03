from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...common.protocol.tasks import ExecutionInput
from ..agent.get_agent import get_agent
from ..task.get_task import get_task
from ..tools.list_tools import list_tools
from ..utils import (
    cozo_query,
    make_cozo_json_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)
from .get_execution import get_execution


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(ExecutionInput, one=True)
@cozo_query(debug=True)
@beartype
def prepare_execution_input(
    *,
    developer_id: UUID,
    task_id: UUID,
    execution_id: UUID,
) -> tuple[list[str], dict]:
    execution_query, execution_params = get_execution.__wrapped__(
        execution_id=execution_id
    )

    # Remove the outer curly braces
    execution_query = execution_query.strip()[1:-1]

    execution_fields = (
        "id",
        "task_id",
        "status",
        "input",
        "session_id",
        "metadata",
        "created_at",
        "updated_at",
    )
    execution_query += f"""
    :create _execution {{
      {", ".join(execution_fields)}
    }}
    """

    task_query, task_params = get_task.__wrapped__(
        developer_id=developer_id, task_id=task_id
    )

    # Remove the outer curly braces
    task_query = task_query.strip()[1:-1]

    task_fields = (
        "id",
        "agent_id",
        "name",
        "description",
        "input_schema",
        "tools",
        "inherit_tools",
        "workflows",
        "created_at",
        "updated_at",
        "metadata",
    )
    task_query += f"""
    :create _task {{
      {", ".join(task_fields)}
    }}
    """

    dummy_agent_id = UUID(int=0)

    [*_, agent_query], agent_params = get_agent.__wrapped__(
        developer_id=developer_id,
        agent_id=dummy_agent_id,  # We will replace this with value from the query
    )
    agent_params.pop("agent_id")
    agent_query = agent_query.replace(
        "<- [[to_uuid($agent_id)]]", ":= *_task { agent_id }"
    )

    agent_fields = (
        "id",
        "name",
        "model",
        "about",
        "metadata",
        "default_settings",
        "instructions",
        "created_at",
        "updated_at",
    )

    agent_query += f"""
    :create _agent {{
      {", ".join(agent_fields)}
    }}
    """

    [*_, tools_query], tools_params = list_tools.__wrapped__(
        developer_id=developer_id,
        agent_id=dummy_agent_id,  # We will replace this with value from the query
    )
    tools_params.pop("agent_id")
    tools_query = tools_query.replace(
        "<- [[to_uuid($agent_id)]]", ":= *_task { agent_id }"
    )

    tools_fields = (
        "id",
        "agent_id",
        "name",
        "type",
        "spec",
        "created_at",
        "updated_at",
    )
    tools_query += f"""
    :create _tools {{
      {", ".join(tools_fields)}
    }}
    """

    combine_query = f"""
    collected_tools[collect(tool)] :=
      *_tools {{ {', '.join(tools_fields)} }},
      tool = {{ {make_cozo_json_query(tools_fields)} }}

    agent_json[agent] :=
      *_agent {{ {', '.join(agent_fields)} }},
      agent = {{ {make_cozo_json_query(agent_fields)} }}

    task_json[task] :=
      *_task {{ {', '.join(task_fields)} }},
      task = {{ {make_cozo_json_query(task_fields)} }}

    execution_json[execution] :=
      *_execution {{ {', '.join(execution_fields)} }},
      execution = {{ {make_cozo_json_query(execution_fields)} }}

    ?[developer_id, execution, task, agent, user, session, tools] :=
      developer_id = to_uuid($developer_id),

      agent_json[agent],
      task_json[task],
      execution_json[execution],
      collected_tools[tools],

      # TODO: Enable these later
      user = null,
      session = null,
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "tasks", task_id=task_id, parents=[("agents", "agent_id")]
        ),
        execution_query,
        task_query,
        agent_query,
        tools_query,
        combine_query,
    ]

    return (
        queries,
        {
            "developer_id": str(developer_id),
            "task_id": str(task_id),
            "execution_id": str(execution_id),
            **execution_params,
            **task_params,
            **agent_params,
            **tools_params,
        },
    )
