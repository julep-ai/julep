from uuid import UUID

from ..utils import cozo_query

from beartype import beartype


@cozo_query
@beartype
def get_execution_input_query(
    task_id: UUID,
    execution_id: UUID,
) -> tuple[str, dict]:
    query = """
{
    ?[task_id, execution_id, status, arguments, session_id, created_at, updated_at] := *executions {
        task_id,
        execution_id,
        status,
        arguments,
        session_id,
        created_at,
        updated_at,
    },
    task_id = to_uuid($task_id),
    execution_id = to_uuid($execution_id),

    :create _execution {
        task_id,
        execution_id,
        created_at,
        updated_at,
        arguments,
        session_id,
        status,
    }
}
{
    ?[task_id, agent_id, name, description, input_schema, tools_available, workflows, updated_at, created_at] := *tasks {
        task_id,
        agent_id,
        name,
        description,
        input_schema,
        tools_available,
        workflows,
        created_at,
        updated_at_ms,
    }, updated_at = to_int(updated_at_ms) / 1000,
       task_id = to_uuid($task_id),

    :create _task {
        task_id,
        agent_id,
        name,
        description,
        input_schema,
        tools_available,
        workflows,
        created_at,
        updated_at,
    }
}
{
    ?[tool_id, name, description, parameters, created_at, updated_at] :=
      *_task { agent_id },
      *agent_functions {
        agent_id,
        tool_id,
        name,
        description,
        parameters,
        created_at,
        updated_at,
      }

    :create _tools {
        tool_id,
        name,
        description,
        parameters,
        created_at,
        updated_at,
    }
}

{
    ?[agent_id, name, about, default_settings, model, metadata, instructions, created_at, updated_at] :=
      *_task { agent_id },
      *agents {
        agent_id,
        name,
        about,
        model,
        metadata,
        instructions, 
        created_at,
        updated_at,
      },
      *agent_default_settings {
        agent_id,
        frequency_penalty,
        presence_penalty,
        length_penalty,
        repetition_penalty,
        top_p,
        temperature,
        min_p,
      },
      default_settings = {
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
        "length_penalty": length_penalty,
        "repetition_penalty": repetition_penalty,
        "top_p": top_p,
        "temperature": temperature,
        "min_p": min_p,
      }

    :create _agent {
        agent_id,
        name,
        about,
        default_settings,
        model,
        metadata,
        instructions, 
        created_at,
        updated_at,
    }
}

{
    ?[session_id, user_id, situation, summary, metadata, created_at, updated_at] :=
      *_task { agent_id },
      *session_lookup {
        agent_id,
        user_id,
        session_id,
      },
      *sessions {
        session_id,
        situation,
        summary,
        metadata,
        created_at,
        updated_at,
      }

    :create _session {
        session_id,
        user_id,
        situation,
        summary,
        metadata,
        created_at,
        updated_at,
    }
}

{
    ?[user_id, name, about, metadata, created_at, updated_at] :=
      *_session { user_id },
      *users {
        user_id,
        name,
        about,
        metadata,
        created_at,
        updated_at,
      }

    :create _user {
        user_id,
        name,
        about,
        metadata,
        created_at,
        updated_at,
    }
}

{
    collected_tools[collect(tool)] :=
      *_tools {
        tool_id,
        name: tool_name,
        description: tool_description,
        parameters: tool_parameters,
        created_at: tool_created_at,
        updated_at: tool_updated_at,
      },
      tool = {
        "id": tool_id,
        "name": tool_name,
        "description": tool_description,
        "parameters": tool_parameters,
        "created_at": tool_created_at,
        "updated_at": tool_updated_at,
      }

    found_users[collect(user)] :=
      *_user {
        user_id,
        name,
        about,
        metadata,
        created_at,
        updated_at,
      },
      user = {
        "id": user_id,
        "name": name,
        "about": about,
        "metadata": metadata,
        "created_at": created_at,
        "updated_at": updated_at,
      }

    found_sessions[collect(session)] :=
      found_users[_users],
      *_agent { agent_id },
      *_session {
        session_id,
        situation,
        summary,
        metadata,
        created_at,
        updated_at,
      },
      session = {
        "id": session_id,
        "agent_id": agent_id,
        "user_id": if(to_bool(_users), _users->0->"user_id"),
        "situation": situation,
        "summary": summary,
        "metadata": metadata,
        "created_at": created_at,
        "updated_at": updated_at,
      }

    ?[execution, task, agent, user, session, tools] :=
      collected_tools[tools],
      found_sessions[_sessions],
      found_users[_users],
      session = _sessions->0,
      user = _users->0,

      *_agent {
        agent_id,
        name: agent_name,
        about: agent_about,
        default_settings: agent_default_settings,
        model: agent_model,
        metadata: agent_metadata,
        instructions: agent_instructions,
        created_at: agent_created_at,
        updated_at: agent_updated_at,
      },
      agent = {
        "id": agent_id,
        "name": agent_name,
        "about": agent_about,
        "default_settings": agent_default_settings,
        "model": agent_model,
        "metadata": agent_metadata,
        "instructions": agent_instructions,
        "created_at": agent_created_at,
        "updated_at": agent_updated_at,
      },

      *_task {
        task_id,
        name: task_name,
        description: task_description,
        input_schema: task_input_schema,
        tools_available: task_tools_available,
        workflows: task_workflows,
        created_at: task_created_at,
        updated_at: task_updated_at,
      },
      task = {
        "id": task_id,
        "agent_id": agent_id,
        "name": task_name,
        "description": task_description,
        "input_schema": task_input_schema,
        "tools_available": task_tools_available,
        "workflows": task_workflows,
        "created_at": task_created_at,
        "updated_at": task_updated_at,
      },

      *_execution {
        execution_id,
        created_at: execution_created_at,
        updated_at: execution_updated_at,
        arguments: execution_arguments,
        session_id: execution_session_id,
        status: execution_status,
      },
      execution = {
        "id": execution_id,
        "task_id": task_id,
        "user_id": if(to_bool(_users), _users->0->"user_id"),
        "created_at": execution_created_at,
        "updated_at": execution_updated_at,
        "arguments": execution_arguments,
        "session_id": execution_session_id,
        "status": execution_status,
      },

}

"""
    return (
        query,
        {
            "task_id": str(task_id),
            "execution_id": str(execution_id),
        },
    )
