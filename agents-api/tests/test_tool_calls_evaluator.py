from uuid import UUID

from agents_api.autogen.openapi_model import CreateSessionRequest
from agents_api.clients.pg import create_db_pool
from agents_api.queries.sessions.create_session import create_session
from uuid_extensions import uuid7
from ward import test

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
                    "name": "user.docs.list",
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
                        "name": "user.docs.create",
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
                        "name": "user.docs.delete",
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
                    "name": "user.docs.search",
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


@test("chat: evaluate user.docs.list tool call")
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


@test("chat: evaluate user.docs.create tool call")
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


@test("chat: evaluate user.docs.delete tool call")
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


@test("chat: evaluate user.docs.search tool call")
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
