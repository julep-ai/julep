from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from agents_api.autogen.openapi_model import (
    CreateSessionRequest,
    HybridDocSearchRequest,
    TextOnlyDocSearchRequest,
    UpdateSessionRequest,
    VectorDocSearchRequest,
)
from agents_api.clients.pg import create_db_pool
from agents_api.queries.sessions.create_session import create_session
from agents_api.routers.utils.tools import ToolCallsEvaluator
from uuid_extensions import uuid7
from ward import raises, test

from tests.fixtures import (
    make_acompletion_multiple_outputs,
    make_request,
    pg_dsn,
    test_agent,
    test_developer_id,
    test_user,
)

agent_doc_list = make_acompletion_multiple_outputs([
    {
        "role": "assistant",
        "content": "Listing agent docs",
        "tool_calls": [
            {
                "id": "call_agent_doc_list",
                "type": "system",
                "function": {
                    "name": "agent.doc.list",
                    "arguments": {
                        "owner_id": str(uuid7()),
                        "developer_id": str(UUID(int=0)),
                        "owner_type": "agent",
                    },
                },
            }
        ],
    },
    {
        "role": "assistant",
        "content": "Here are the agent docs",
    },
])

agent_doc_create = make_acompletion_multiple_outputs(
    lambda agent, **_: [
        {
            "role": "assistant",
            "content": "Creating agent doc",
            "tool_calls": [
                {
                    "id": "call_agent_doc_create",
                    "type": "system",
                    "function": {
                        "name": "agent.doc.create",
                        "arguments": {
                            "agent_id": str(agent.id),
                            "x_developer_id": str(UUID(int=0)),
                            "data": {"title": "Test Doc", "content": "This is a test document"},
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Agent doc created successfully",
        },
    ]
)

agent_doc_delete = make_acompletion_multiple_outputs(
    lambda agent, doc, **_: [
        {
            "role": "assistant",
            "content": "Deleting agent doc",
            "tool_calls": [
                {
                    "id": "call_agent_doc_delete",
                    "type": "system",
                    "function": {
                        "name": "agent.doc.delete",
                        "arguments": {
                            "doc_id": str(doc.id),
                            "developer_id": str(UUID(int=0)),
                            "owner_type": "agent",
                            "owner_id": str(agent.id),
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Agent doc deleted successfully",
        },
    ]
)

agent_doc_search = make_acompletion_multiple_outputs(
    lambda agent, **_: [
        {
            "role": "assistant",
            "content": "Searching agent docs",
            "tool_calls": [
                {
                    "id": "call_agent_doc_search",
                    "type": "system",
                    "function": {
                        "name": "agent.doc.search",
                        "arguments": {
                            "agent_id": str(agent.id),
                            "x_developer_id": str(UUID(int=0)),
                            "search_params": {
                                "text": "any string",
                            },
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Here are the search results",
        },
    ]
)

agent_list = make_acompletion_multiple_outputs([
    {
        "role": "assistant",
        "content": "Listing agents",
        "tool_calls": [
            {
                "id": "call_agent_list",
                "type": "system",
                "function": {
                    "name": "agent.list",
                    "arguments": {"developer_id": str(UUID(int=0))},
                },
            }
        ],
    },
    {
        "role": "assistant",
        "content": "Here are the agents",
    },
])

agent_get = make_acompletion_multiple_outputs(
    lambda agent, **_: [
        {
            "role": "assistant",
            "content": "Getting agent details",
            "tool_calls": [
                {
                    "id": "call_agent_get",
                    "type": "system",
                    "function": {
                        "name": "agent.get",
                        "arguments": {
                            "agent_id": str(agent.id),
                            "developer_id": str(UUID(int=0)),
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Here are the agent details",
        },
    ]
)

agent_create = make_acompletion_multiple_outputs([
    {
        "role": "assistant",
        "content": "Creating agent",
        "tool_calls": [
            {
                "id": "call_agent_create",
                "type": "system",
                "function": {
                    "name": "agent.create",
                    "arguments": {
                        "data": {
                            "name": "test agent 2",
                            "canonical_name": f"some_unique_name_{str(uuid7()).split('-')[0]}",
                            "model": "gpt-4o-mini",
                            "about": "test agent about 2",
                            "metadata": {"test": "test 2"},
                        },
                        "developer_id": str(UUID(int=0)),
                        "agent_id": str(uuid7()),
                    },
                },
            }
        ],
    },
    {
        "role": "assistant",
        "content": "Agent created successfully",
    },
])

agent_update = make_acompletion_multiple_outputs(
    lambda agent, **_: [
        {
            "role": "assistant",
            "content": "Updating agent",
            "tool_calls": [
                {
                    "id": "call_agent_update",
                    "type": "system",
                    "function": {
                        "name": "agent.update",
                        "arguments": {
                            "agent_id": str(agent.id),
                            "developer_id": str(UUID(int=0)),
                            "data": {"name": "Updated Agent", "about": "Updated description"},
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Agent updated successfully",
        },
    ]
)

agent_delete = make_acompletion_multiple_outputs(
    lambda agent, **_: [
        {
            "role": "assistant",
            "content": "Deleting agent",
            "tool_calls": [
                {
                    "id": "call_agent_delete",
                    "type": "system",
                    "function": {
                        "name": "agent.delete",
                        "arguments": {
                            "agent_id": str(agent.id),
                            "developer_id": str(UUID(int=0)),
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Agent deleted successfully",
        },
    ]
)

user_doc_list = make_acompletion_multiple_outputs([
    {
        "role": "assistant",
        "content": "Listing user docs",
        "tool_calls": [
            {
                "id": "call_user_doc_list",
                "type": "system",
                "function": {
                    "name": "user.doc.list",
                    "arguments": {
                        "owner_id": str(uuid7()),
                        "developer_id": str(UUID(int=0)),
                        "owner_type": "user",
                    },
                },
            }
        ],
    },
    {
        "role": "assistant",
        "content": "Here are the user docs",
    },
])

user_doc_create = make_acompletion_multiple_outputs(
    lambda user, **_: [
        {
            "role": "assistant",
            "content": "Creating user doc",
            "tool_calls": [
                {
                    "id": "call_user_doc_create",
                    "type": "system",
                    "function": {
                        "name": "user.doc.create",
                        "arguments": {
                            "user_id": str(user.id),
                            "x_developer_id": str(UUID(int=0)),
                            "data": {"title": "User Doc", "content": "This is a user document"},
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "User doc created successfully",
        },
    ]
)

user_doc_delete = make_acompletion_multiple_outputs(
    lambda user, user_doc, **_: [
        {
            "role": "assistant",
            "content": "Deleting user doc",
            "tool_calls": [
                {
                    "id": "call_user_doc_delete",
                    "type": "system",
                    "function": {
                        "name": "user.doc.delete",
                        "arguments": {
                            "doc_id": str(user_doc.id),
                            "developer_id": str(UUID(int=0)),
                            "owner_type": "user",
                            "owner_id": str(user.id),
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "User doc deleted successfully",
        },
    ]
)

user_doc_search = make_acompletion_multiple_outputs([
    {
        "role": "assistant",
        "content": "Searching user docs",
        "tool_calls": [
            {
                "id": "call_user_doc_search",
                "type": "system",
                "function": {
                    "name": "user.doc.search",
                    "arguments": {
                        "user_id": str(uuid7()),
                        "x_developer_id": str(UUID(int=0)),
                        "search_params": {"text": "test query"},
                    },
                },
            }
        ],
    },
    {
        "role": "assistant",
        "content": "Here are the search results",
    },
])

user_list = make_acompletion_multiple_outputs([
    {
        "role": "assistant",
        "content": "Listing users",
        "tool_calls": [
            {
                "id": "call_user_list",
                "type": "system",
                "function": {
                    "name": "user.list",
                    "arguments": {"developer_id": str(UUID(int=0))},
                },
            }
        ],
    },
    {
        "role": "assistant",
        "content": "Here are the users",
    },
])

user_get = make_acompletion_multiple_outputs(
    lambda user, **_: [
        {
            "role": "assistant",
            "content": "Getting user details",
            "tool_calls": [
                {
                    "id": "call_user_get",
                    "type": "system",
                    "function": {
                        "name": "user.get",
                        "arguments": {
                            "user_id": str(user.id),
                            "developer_id": str(UUID(int=0)),
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Here are the user details",
        },
    ]
)

user_create = make_acompletion_multiple_outputs([
    {
        "role": "assistant",
        "content": "Creating user",
        "tool_calls": [
            {
                "id": "call_user_create",
                "type": "system",
                "function": {
                    "name": "user.create",
                    "arguments": {
                        "developer_id": str(UUID(int=0)),
                        "data": {"name": "Test User", "about": "Test user description"},
                    },
                },
            }
        ],
    },
    {
        "role": "assistant",
        "content": "User created successfully",
    },
])

user_update = make_acompletion_multiple_outputs(
    lambda user, **_: [
        {
            "role": "assistant",
            "content": "Updating user",
            "tool_calls": [
                {
                    "id": "call_user_update",
                    "type": "system",
                    "function": {
                        "name": "user.update",
                        "arguments": {
                            "user_id": str(user.id),
                            "developer_id": str(UUID(int=0)),
                            "data": {
                                "name": "Updated User",
                                "about": "Updated user description",
                            },
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "User updated successfully",
        },
    ]
)

user_delete = make_acompletion_multiple_outputs(
    lambda user, **_: [
        {
            "role": "assistant",
            "content": "Deleting user",
            "tool_calls": [
                {
                    "id": "call_user_delete",
                    "type": "system",
                    "function": {
                        "name": "user.delete",
                        "arguments": {
                            "user_id": str(user.id),
                            "developer_id": str(UUID(int=0)),
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "User deleted successfully",
        },
    ]
)

session_list = make_acompletion_multiple_outputs([
    {
        "role": "assistant",
        "content": "Listing sessions",
        "tool_calls": [
            {
                "id": "call_session_list",
                "type": "system",
                "function": {
                    "name": "session.list",
                    "arguments": {"developer_id": str(UUID(int=0))},
                },
            }
        ],
    },
    {
        "role": "assistant",
        "content": "Here are the sessions",
    },
])

session_get = make_acompletion_multiple_outputs(
    lambda session, **_: [
        {
            "role": "assistant",
            "content": "Getting session details",
            "tool_calls": [
                {
                    "id": "call_session_get",
                    "type": "system",
                    "function": {
                        "name": "session.get",
                        "arguments": {
                            "session_id": str(session.id),
                            "developer_id": str(UUID(int=0)),
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Here are the session details",
        },
    ]
)

session_create = make_acompletion_multiple_outputs(
    lambda agent, **_: [
        {
            "role": "assistant",
            "content": "Creating session",
            "tool_calls": [
                {
                    "id": "call_session_create",
                    "type": "system",
                    "function": {
                        "name": "session.create",
                        "arguments": {
                            "developer_id": str(UUID(int=0)),
                            "session_id": str(uuid7()),
                            "data": {"agent": str(agent.id), "situation": "Test session"},
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Session created successfully",
        },
    ]
)

session_update = make_acompletion_multiple_outputs(
    lambda agent, doc, user, task, user_doc, session: [
        {
            "role": "assistant",
            "content": "Updating session",
            "tool_calls": [
                {
                    "id": "call_session_update",
                    "type": "system",
                    "function": {
                        "name": "session.update",
                        "arguments": {
                            "session_id": str(session.id),
                            "developer_id": str(UUID(int=0)),
                            "data": {"situation": "Updated session situation"},
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Session updated successfully",
        },
    ]
)

session_history = make_acompletion_multiple_outputs([
    {
        "role": "assistant",
        "content": "Getting session history",
        "tool_calls": [
            {
                "id": "call_session_history",
                "type": "system",
                "function": {
                    "name": "session.history",
                    "arguments": {"session_id": str(uuid7()), "developer_id": str(UUID(int=0))},
                },
            }
        ],
    },
    {
        "role": "assistant",
        "content": "Here is the session history",
    },
])

task_list = make_acompletion_multiple_outputs([
    {
        "role": "assistant",
        "content": "Listing tasks",
        "tool_calls": [
            {
                "id": "call_task_list",
                "type": "system",
                "function": {
                    "name": "task.list",
                    "arguments": {"developer_id": str(UUID(int=0)), "agent_id": str(uuid7())},
                },
            }
        ],
    },
    {
        "role": "assistant",
        "content": "Here are the tasks",
    },
])

task_get = make_acompletion_multiple_outputs(
    lambda task, **_: [
        {
            "role": "assistant",
            "content": "Getting task details",
            "tool_calls": [
                {
                    "id": "call_task_get",
                    "type": "system",
                    "function": {
                        "name": "task.get",
                        "arguments": {
                            "task_id": str(task.id),
                            "developer_id": str(UUID(int=0)),
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Here are the task details",
        },
    ]
)

task_create = make_acompletion_multiple_outputs(
    lambda agent, **_: [
        {
            "role": "assistant",
            "content": "Creating task",
            "tool_calls": [
                {
                    "id": "call_task_create",
                    "type": "system",
                    "function": {
                        "name": "task.create",
                        "arguments": {
                            "developer_id": str(UUID(int=0)),
                            "agent_id": str(agent.id),
                            "data": {"name": "Test Task", "main": [{"sleep": {"seconds": 1}}]},
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Task created successfully",
        },
    ]
)

task_update = make_acompletion_multiple_outputs(
    lambda agent, task, **_: [
        {
            "role": "assistant",
            "content": "Updating task",
            "tool_calls": [
                {
                    "id": "call_task_update",
                    "type": "system",
                    "function": {
                        "name": "task.update",
                        "arguments": {
                            "task_id": str(task.id),
                            "agent_id": str(agent.id),
                            "developer_id": str(UUID(int=0)),
                            "data": {
                                "name": "Updated Task",
                                "main": [{"sleep": {"seconds": 1}}],
                            },
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Task updated successfully",
        },
    ]
)

task_delete = make_acompletion_multiple_outputs(
    lambda task, **_: [
        {
            "role": "assistant",
            "content": "Deleting task",
            "tool_calls": [
                {
                    "id": "call_task_delete",
                    "type": "system",
                    "function": {
                        "name": "task.delete",
                        "arguments": {
                            "task_id": str(task.id),
                            "developer_id": str(UUID(int=0)),
                        },
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Task deleted successfully",
        },
    ]
)


@test("chat: evaluate agent.doc.list tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=agent_doc_list,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate agent.doc.create tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=agent_doc_create,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate agent.doc.delete tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=agent_doc_delete,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate agent.doc.search tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=agent_doc_search,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate agent.list tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=agent_list,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate agent.get tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=agent_get,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate agent.create tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=agent_create,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate agent.update tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=agent_update,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate agent.delete tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=agent_delete,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate user.doc.list tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=user_doc_list,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate user.doc.create tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=user_doc_create,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate user.doc.delete tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    user=test_user,
    mocks=user_doc_delete,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            user=user.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate user.doc.search tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=user_doc_search,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate user.list tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=user_list,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate user.get tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=user_get,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate user.create tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=user_create,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate user.update tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=user_update,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate user.delete tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=user_delete,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate session.list tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=session_list,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate session.get tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=session_get,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate session.create tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=session_create,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate session.update tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=session_update,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate session.history tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=session_history,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate task.list tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=task_list,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate task.get tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=task_get,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate task.create tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=task_create,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate task.update tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=task_update,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("chat: evaluate task.delete tool call")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=task_delete,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (_embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 201
    assert acompletion.call_count == 2


@test("ToolCallsEvaluator: test _create_search_request for hybrid search")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    search_params = {
        "text": "test query",
        "vector": [0.1, 0.2, 0.3],
        "mmr_strength": 0.5,
        "alpha": 0.8,
        "confidence": 0.6,
        "limit": 5,
    }
    result = evaluator._create_search_request(search_params)
    assert isinstance(result, HybridDocSearchRequest)
    assert result.text == "test query"
    assert result.vector == [0.1, 0.2, 0.3]
    assert result.mmr_strength == 0.5
    assert result.alpha == 0.8
    assert result.confidence == 0.6
    assert result.limit == 5


@test("ToolCallsEvaluator: test _create_search_request for text-only search")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    search_params = {
        "text": "test query",
        "mmr_strength": 0.5,
        "limit": 5,
    }
    result = evaluator._create_search_request(search_params)
    assert isinstance(result, TextOnlyDocSearchRequest)
    assert result.text == "test query"
    assert result.mmr_strength == 0.5
    assert result.limit == 5


@test("ToolCallsEvaluator: test _create_search_request for vector-only search")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    search_params = {
        "vector": [0.1, 0.2, 0.3],
        "mmr_strength": 0.5,
        "confidence": 0.6,
        "limit": 5,
    }
    result = evaluator._create_search_request(search_params)
    assert isinstance(result, VectorDocSearchRequest)
    assert result.vector == [0.1, 0.2, 0.3]
    assert result.mmr_strength == 0.5
    assert result.confidence == 0.6
    assert result.limit == 5


@test("ToolCallsEvaluator: test _create_search_request with no valid parameters")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    search_params = {"invalid": "params"}
    result = evaluator._create_search_request(search_params)
    assert result is None


@test("ToolCallsEvaluator: test _call_tool for agent.create")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    developer_id = uuid4()
    tool_name = "agent.create"
    arguments = {
        "x_developer_id": str(developer_id),
        "data": {
            "name": "Test Agent",
            "model": "gpt-4",
            "instructions": "Test instructions",
            "metadata": {"key": "value"},
            "settings": {"setting1": "value1"}
        }
    }
    mock_handler = AsyncMock(return_value={"id": "agent_id"})

    with patch.dict(evaluator.system_tool_handlers, {"agent.create": mock_handler}):
        result = await evaluator._call_tool(developer_id, tool_name, arguments)
        assert result == {"id": "agent_id"}
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args[1]
        assert isinstance(call_args["data"], dict)
        assert call_args["x_developer_id"] == developer_id
        assert call_args["data"]["name"] == "Test Agent"
        assert call_args["data"]["model"] == "gpt-4"
        assert call_args["data"]["instructions"] == "Test instructions"
        assert call_args["data"]["metadata"] == {"key": "value"}
        assert call_args["data"]["settings"] == {"setting1": "value1"}


@test("ToolCallsEvaluator: test _call_tool for agent.doc.search")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    developer_id = uuid4()
    tool_name = "agent.doc.search"
    arguments = {
        "developer_id": developer_id,
        "agent_id": str(uuid4()),
        "search_params": {
            "text": "test query",
            "vector": [0.1, 0.2, 0.3],
        },
    }
    mock_handler = AsyncMock(return_value={"results": []})
    with patch.dict(evaluator.system_tool_handlers, {"agent.doc.search": mock_handler}):
        result = await evaluator._call_tool(developer_id, tool_name, arguments)
        assert result == {"results": []}
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args[1]
        assert isinstance(call_args["search_params"], HybridDocSearchRequest)
        assert call_args["x_developer_id"] == developer_id


@test("ToolCallsEvaluator: test _call_tool for session.chat")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    developer_id = uuid4()
    session_id = uuid4()
    tool_name = "session.chat"
    arguments = {
        "x_developer_id": str(developer_id),
        "session_id": str(session_id),
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    }
    mock_handler = AsyncMock(return_value={"response": "test"})

    with patch.dict(evaluator.system_tool_handlers, {"session.chat": mock_handler}):
        result = await evaluator._call_tool(developer_id, tool_name, arguments)
        assert result == {"response": "test"}
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args[1]
        assert isinstance(call_args["messages"], list)
        assert call_args["x_developer_id"] == developer_id
        assert call_args["session_id"] == session_id
        assert len(call_args["messages"]) == 2
        assert call_args["messages"][0]["role"] == "user"
        assert call_args["messages"][0]["content"] == "Hello"
        assert call_args["messages"][1]["role"] == "assistant"
        assert call_args["messages"][1]["content"] == "Hi there!"


@test("ToolCallsEvaluator: test _call_tool for session.create")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    developer_id = uuid4()
    tool_name = "session.create"
    arguments = {
        "developer_id": developer_id,
        "session_id": str(uuid4()),
        "data": {
            "name": "test session",
            "metadata": {"key": "value"},
        },
    }
    mock_handler = AsyncMock(return_value={"id": "session_id"})
    with patch.dict(evaluator.system_tool_handlers, {"session.create": mock_handler}):
        result = await evaluator._call_tool(developer_id, tool_name, arguments)
        assert result == {"id": "session_id"}
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args[1]
        assert isinstance(call_args["data"], CreateSessionRequest)
        assert call_args["developer_id"] == developer_id


@test("ToolCallsEvaluator: test _call_tool for session.update")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    developer_id = uuid4()
    tool_name = "session.update"
    arguments = {
        "developer_id": developer_id,
        "session_id": str(uuid4()),
        "name": "updated session",
        "metadata": {"key": "value"},
    }
    mock_handler = AsyncMock(return_value={"id": "session_id"})
    with patch.dict(evaluator.system_tool_handlers, {"session.update": mock_handler}):
        result = await evaluator._call_tool(developer_id, tool_name, arguments)
        assert result == {"id": "session_id"}
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args[1]
        assert isinstance(call_args["data"], UpdateSessionRequest)
        assert call_args["developer_id"] == developer_id


@test("ToolCallsEvaluator: test _call_tool for agent.update")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    developer_id = uuid4()
    agent_id = uuid4()
    tool_name = "agent.update"
    arguments = {
        "x_developer_id": str(developer_id),
        "agent_id": str(agent_id),
        "data": {
            "name": "Updated Agent",
            "model": "gpt-4-turbo",
            "instructions": "Updated instructions",
            "metadata": {"key": "updated_value"},
            "settings": {"setting1": "updated_value1"}
        }
    }
    mock_handler = AsyncMock(return_value={"id": "agent_id"})

    with patch.dict(evaluator.system_tool_handlers, {"agent.update": mock_handler}):
        result = await evaluator._call_tool(developer_id, tool_name, arguments)
        assert result == {"id": "agent_id"}
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args[1]
        assert isinstance(call_args["data"], dict)
        assert call_args["x_developer_id"] == developer_id
        assert call_args["agent_id"] == agent_id
        assert call_args["data"]["name"] == "Updated Agent"
        assert call_args["data"]["model"] == "gpt-4-turbo"
        assert call_args["data"]["instructions"] == "Updated instructions"
        assert call_args["data"]["metadata"] == {"key": "updated_value"}
        assert call_args["data"]["settings"] == {"setting1": "updated_value1"}


@test("ToolCallsEvaluator: test _call_tool for agent.delete")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    developer_id = uuid4()
    agent_id = uuid4()
    tool_name = "agent.delete"
    arguments = {
        "x_developer_id": str(developer_id),
        "agent_id": str(agent_id)
    }
    mock_handler = AsyncMock(return_value={"success": True})

    with patch.dict(evaluator.system_tool_handlers, {"agent.delete": mock_handler}):
        result = await evaluator._call_tool(developer_id, tool_name, arguments)
        assert result == {"success": True}
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args[1]
        assert call_args["x_developer_id"] == str(developer_id)
        assert call_args["agent_id"] == agent_id


@test("ToolCallsEvaluator: test _call_tool for session.delete")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    developer_id = uuid4()
    session_id = uuid4()
    tool_name = "session.delete"
    arguments = {
        "x_developer_id": str(developer_id),
        "session_id": str(session_id)
    }
    mock_handler = AsyncMock(return_value={"success": True})

    with patch.dict(evaluator.system_tool_handlers, {"session.delete": mock_handler}):
        result = await evaluator._call_tool(developer_id, tool_name, arguments)
        assert result == {"success": True}
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args[1]
        assert call_args["x_developer_id"] == str(developer_id)
        assert call_args["session_id"] == session_id


@test("ToolCallsEvaluator: test _call_tool with invalid tool name format")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    developer_id = uuid4()
    tool_name = "invalid"
    arguments = {"x_developer_id": str(developer_id)}
    with raises(NotImplementedError) as exc:
        await evaluator._call_tool(developer_id, tool_name, arguments)
    assert str(exc.raised) == "System call not implemented for invalid"


@test("ToolCallsEvaluator: test peek_first_chunk with valid stream")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    mock_chunk1 = MagicMock()
    mock_chunk2 = MagicMock()

    async def gen():
        yield mock_chunk1
        yield mock_chunk2

    result, gen = await evaluator.peek_first_chunk(gen())
    assert result == mock_chunk1
    assert gen is not None

    # Verify generator yields chunks in correct order
    chunks = [chunk async for chunk in gen]
    assert len(chunks) == 2
    assert chunks[0] == mock_chunk1
    assert chunks[1] == mock_chunk2


@test("ToolCallsEvaluator: test peek_first_chunk with empty stream")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    mock_stream = AsyncMock()
    mock_stream.__anext__.side_effect = StopAsyncIteration
    result, gen = await evaluator.peek_first_chunk(mock_stream)
    assert result is None
    assert gen == mock_stream


@test("ToolCallsEvaluator: test peek_first_chunk with single chunk stream")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    mock_chunk = MagicMock()

    async def gen():
        yield mock_chunk

    result, gen = await evaluator.peek_first_chunk(gen())
    assert result == mock_chunk
    assert gen is not None

    # Verify generator yields only one chunk
    chunks = [chunk async for chunk in gen]
    assert len(chunks) == 1
    assert chunks[0] == mock_chunk
