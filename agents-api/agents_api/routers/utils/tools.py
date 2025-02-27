import json
from collections.abc import Awaitable, Callable
from functools import partial, wraps
from typing import Any
from uuid import UUID

from beartype import beartype
from fastapi.background import BackgroundTasks
from litellm.utils import CustomStreamWrapper, ModelResponse

from ...app import app
from ...autogen.openapi_model import (
    ChatInput,
    CreateAgentRequest,
    CreateDocRequest,
    CreateSessionRequest,
    HybridDocSearchRequest,
    TextOnlyDocSearchRequest,
    UpdateSessionRequest,
    UpdateUserRequest,
    VectorDocSearchRequest,
    CreateUserRequest,
    CreateTaskRequest,
    UpdateTaskRequest,
)
from ...queries.agents.create_agent import create_agent as create_agent_query
from ...queries.agents.delete_agent import delete_agent as delete_agent_query
from ...queries.agents.get_agent import get_agent as get_agent_query
from ...queries.agents.list_agents import list_agents as list_agents_query
from ...queries.agents.update_agent import update_agent as update_agent_query
from ...queries.developers import get_developer
from ...queries.docs.delete_doc import delete_doc as delete_doc_query
from ...queries.docs.list_docs import list_docs as list_docs_query
from ...queries.entries.get_history import get_history as get_history_query
from ...queries.sessions.create_session import create_session as create_session_query
from ...queries.sessions.get_session import get_session as get_session_query
from ...queries.sessions.list_sessions import list_sessions as list_sessions_query
from ...queries.sessions.update_session import update_session as update_session_query
from ...queries.tasks.create_task import create_task as create_task_query
from ...queries.tasks.delete_task import delete_task as delete_task_query
from ...queries.tasks.get_task import get_task as get_task_query
from ...queries.tasks.list_tasks import list_tasks as list_tasks_query
from ...queries.tasks.update_task import update_task as update_task_query
from ...queries.users.create_user import create_user as create_user_query
from ...queries.users.delete_user import delete_user as delete_user_query
from ...queries.users.get_user import get_user as get_user_query
from ...queries.users.list_users import list_users as list_users_query
from ...queries.users.update_user import update_user as update_user_query

# FIXME: Do not use routes directly;
from ...routers.docs.create_doc import create_agent_doc, create_user_doc
from ...routers.docs.search_docs import search_agent_docs, search_user_docs

MIN_TOOL_NAME_SEGMENTS = 2


_system_tool_handlers = {
    "agent.doc.list": list_docs_query,
    "agent.doc.create": create_agent_doc,
    "agent.doc.delete": delete_doc_query,
    "agent.doc.search": search_agent_docs,
    "agent.list": list_agents_query,
    "agent.get": get_agent_query,
    "agent.create": create_agent_query,
    "agent.update": update_agent_query,
    "agent.delete": delete_agent_query,
    "user.doc.list": list_docs_query,
    "user.doc.create": create_user_doc,
    "user.doc.delete": delete_doc_query,
    "user.doc.search": search_user_docs,
    "user.list": list_users_query,
    "user.get": get_user_query,
    "user.create": create_user_query,
    "user.update": update_user_query,
    "user.delete": delete_user_query,
    "session.list": list_sessions_query,
    "session.get": get_session_query,
    "session.create": create_session_query,
    "session.update": update_session_query,
    "session.history": get_history_query,
    "task.list": list_tasks_query,
    "task.get": get_task_query,
    "task.create": create_task_query,
    "task.update": update_task_query,
    "task.delete": delete_task_query,
}


def _create_search_request(arguments: dict) -> Any:
    """Create appropriate search request based on available parameters."""
    if "text" in arguments and "vector" in arguments:
        return HybridDocSearchRequest(
            text=arguments.pop("text"),
            mmr_strength=arguments.pop("mmr_strength", 0),
            vector=arguments.pop("vector"),
            alpha=arguments.pop("alpha", 0.75),
            confidence=arguments.pop("confidence", 0.5),
            limit=arguments.get("limit", 10),
        )
    if "text" in arguments:
        return TextOnlyDocSearchRequest(
            text=arguments.pop("text"),
            mmr_strength=arguments.pop("mmr_strength", 0),
            limit=arguments.get("limit", 10),
        )
    if "vector" in arguments:
        return VectorDocSearchRequest(
            vector=arguments.pop("vector"),
            mmr_strength=arguments.pop("mmr_strength", 0),
            confidence=arguments.pop("confidence", 0.7),
            limit=arguments.get("limit", 10),
        )
    return None


@beartype
async def call_tool(developer_id: UUID, tool_name: str, arguments: dict):
    tool_handler = _system_tool_handlers.get(tool_name)
    if not tool_handler:
        msg = f"System call not implemented for {tool_name}"
        raise NotImplementedError(msg)

    connection_pool = getattr(app.state, "postgres_pool", None)
    tool_handler = partial(tool_handler, connection_pool=connection_pool)
    arguments["developer_id"] = developer_id

    # Convert all UUIDs to UUID objects
    uuid_fields = ["agent_id", "user_id", "task_id", "session_id", "doc_id"]
    for field in uuid_fields:
        if field in arguments:
            fld = arguments[field]
            if isinstance(fld, str):
                arguments[field] = UUID(fld)

    parts = tool_name.split(".")
    if len(parts) < MIN_TOOL_NAME_SEGMENTS:
        msg = f"invalid system tool name: {tool_name}"
        raise NameError(msg)

    resource, subresource, operation = parts[0], None, parts[-1]
    if len(parts) > MIN_TOOL_NAME_SEGMENTS:
        subresource = parts[1]

    if subresource == "doc" and operation not in ["create", "search"]:
        owner_id_field = f"{resource}_id"
        if owner_id_field in arguments:
            doc_args = {
                "owner_type": resource,
                "owner_id": arguments[owner_id_field],
                **arguments,
            }
            doc_args.pop(owner_id_field)
            arguments = doc_args

    # Handle special cases for doc operations
    if operation == "create" and subresource == "doc":
        arguments["x_developer_id"] = arguments.pop("developer_id")
        return await tool_handler(
            data=CreateDocRequest(**arguments.pop("data")),
            **arguments,
        )

    # Handle search operations
    if operation == "search" and subresource == "doc":
        arguments["x_developer_id"] = arguments.pop("developer_id")
        search_params = _create_search_request(arguments)
        return await tool_handler(search_params=search_params, **arguments)

    # Handle chat operations
    if operation == "chat" and resource == "session":
        developer = await get_developer(
            developer_id=arguments["developer_id"],
            connection_pool=connection_pool,
        )  # type: ignore[not-callable]

        session_id = arguments.get("session_id")
        x_custom_api_key = arguments.get("x_custom_api_key", None)
        chat_input = ChatInput(**arguments)
        bg_runner = BackgroundTasks()
        res = await tool_handler(
            developer=developer,
            session_id=session_id,
            background_tasks=bg_runner,
            x_custom_api_key=x_custom_api_key,
            chat_input=chat_input,
        )
        await bg_runner()
        return res

    # Handle create session
    if operation == "create" and resource == "session":
        developer_id = arguments.pop("developer_id")
        session_id = arguments.pop("session_id", None)
        create_session_request = CreateSessionRequest(**arguments)

        return await tool_handler(
            developer_id=developer_id,
            session_id=session_id,
            data=create_session_request,
        )

    # Handle update session
    if operation == "update" and resource == "session":
        developer_id = arguments.pop("developer_id")
        session_id = arguments.pop("session_id")
        update_session_request = UpdateSessionRequest(**arguments)

        return await tool_handler(
            developer_id=developer_id,
            session_id=session_id,
            data=update_session_request,
        )

    # Handle update user
    if operation == "update" and resource == "user":
        return await tool_handler(
            data=UpdateUserRequest(**arguments.pop("data")),
            **arguments,
        )

    # Handle agent operations
    if resource == "agent" and operation in ("create", "update"):
        return await tool_handler(
            data=CreateAgentRequest(**arguments.pop("data")),
            **arguments,
        )

    # Handle user operations
    if resource == "user":
        if operation == "create":
            return await tool_handler(
                data=CreateUserRequest(**arguments.pop("data")),
                **arguments,
            )
        if operation == "update":
            return await tool_handler(
                data=UpdateUserRequest(**arguments.pop("data")),
                **arguments,
            )

    # Handle task operations
    if resource == "task":
        if operation == "create":
            return await tool_handler(
                data=CreateTaskRequest(**arguments.pop("data")),
                **arguments,
            )
        if operation == "update":
            return await tool_handler(
                data=UpdateTaskRequest(**arguments.pop("data")),
                **arguments,
            )

    return await tool_handler(**arguments)


def tool_calls_evaluator(
    *,
    tool_types: set[str],
    developer_id: UUID,
):
    def decor(
        func: Callable[..., Awaitable[ModelResponse | CustomStreamWrapper]],
    ):
        @wraps(func)
        async def wrapper(**kwargs):
            response: ModelResponse | CustomStreamWrapper | None = None
            done = False
            messages = kwargs.get("messages", [])
            while not done:
                response: ModelResponse | CustomStreamWrapper = await func(**kwargs)
                if not response.choices or not response.choices[0].message.tool_calls:
                    return response

                # TODO: add streaming response handling
                for tool in response.choices[0].message.tool_calls:
                    if tool.type not in tool_types:
                        done = True
                        continue

                    done = False
                    # call a tool
                    tool_name = tool.function.name
                    tool_args = json.loads(tool.function.arguments)
                    tool_response = await call_tool(developer_id, tool_name, tool_args)

                    # append result to messages from previous step
                    messages.append({
                        "tool_call_id": tool.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": tool_response,
                    })
                    kwargs["messages"] = messages

            return response

        return wrapper

    return decor
