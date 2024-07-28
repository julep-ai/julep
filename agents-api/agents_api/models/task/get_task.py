from beartype import beartype

from uuid import UUID


from ..utils import (
    cozo_query,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)

from .create_task import spec_to_task


@wrap_in_class(spec_to_task, one=True)
@cozo_query
@beartype
def get_task(
    *,
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID,
) -> tuple[str, dict]:
    get_query = """
    input[agent_id, task_id] <- [[
        to_uuid($agent_id),
        to_uuid($task_id),
    ]]

    task_data[
        task_id,
        agent_id,
        name,
        description,
        input_schema,
        tools,
        inherit_tools,
        workflows,
        created_at,
        updated_at,
        metadata,
    ] := 
        input[agent_id, task_id],
        *tasks {
            agent_id,
            task_id,
            updated_at_ms,
            name,
            description,
            input_schema,
            tools,
            inherit_tools,
            workflows,
            created_at,
            metadata,
            @ 'NOW'
        },
        updated_at = to_int(updated_at_ms) / 1000

    tool_data[collect(tool_def)] :=
        input[agent_id, _],
        *tools {
            agent_id,
            type,
            name,
            spec,
        }, tool_def = {
            "type": type,
            "name": name,
            "spec": spec,
            "inherited": true,
        }

    ?[
        task_id,
        agent_id,
        name,
        description,
        input_schema,
        tools,
        inherit_tools,
        workflows,
        created_at,
        updated_at,
        metadata,
    ] := 
        tool_data[inherited_tools],
        task_data[
            task_id,
            agent_id,
            name,
            description,
            input_schema,
            task_tools,
            inherit_tools,
            workflows,
            created_at,
            updated_at,
            metadata,
        ], tools = task_tools ++ if(inherit_tools, inherited_tools, [])

    :limit 1
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        get_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (query, {"agent_id": str(agent_id), "task_id": str(task_id)})
