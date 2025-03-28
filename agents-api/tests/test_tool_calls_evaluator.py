# ruff: noqa: SLF001
import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from agents_api.app import app
from agents_api.autogen.openapi_model import (
    Agent,
    Doc,
    DocSearchResponse,
    EvaluateStep,
    History,
    HybridDocSearchRequest,
    ResourceDeletedResponse,
    Session,
    TextOnlyDocSearchRequest,
    User,
    VectorDocSearchRequest,
)
from agents_api.routers.utils.tools import ToolCallsEvaluator
from litellm.types.utils import ChatCompletionMessageToolCall, Function, ModelResponse, Choices, Message
from ward import raises, skip, test

from .fixtures import (
    create_db_pool,
    pg_dsn,
    test_agent,
    test_developer,
    test_doc,
    test_session,
    test_task,
    test_user,
    test_user_doc,
)


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


@test("ToolCallsEvaluator: test prepare_tool_call for agent.create")
async def _(dsn=pg_dsn, developer=test_developer):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "agent.create"
    arguments = {
        "developer_id": str(developer.id),
        "data": {
            "name": "Test Agent",
            "model": "gpt-4",
            "instructions": "Test instructions",
            "metadata": {"key": "value"},
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, Agent)
    assert result.name == "Test Agent"
    assert result.model == "gpt-4"
    assert result.instructions == ["Test instructions"]
    assert result.metadata == {"key": "value"}


@test("ToolCallsEvaluator: test prepare_tool_call for agent.update")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "agent.update"
    arguments = {
        "developer_id": str(developer.id),
        "agent_id": str(agent.id),
        "data": {
            "name": "Updated Agent",
            "model": "gpt-4o-mini",
            "instructions": "Updated instructions",
            "about": "Updated about",
            "metadata": {"updated_key": "updated_value"},
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, Agent)
    assert result.name == "Updated Agent"
    assert result.model == "gpt-4o-mini"
    # FIXME: instructions is not updated
    # assert result.instructions == ["Updated instructions"]
    assert result.about == "Updated about"
    assert result.metadata == {"updated_key": "updated_value"}


@test("ToolCallsEvaluator: test prepare_tool_call for agent.get")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "agent.get"
    arguments = {
        "developer_id": str(developer.id),
        "agent_id": str(agent.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, Agent)
    assert result.model == "gpt-4o-mini"
    assert result.name == "test agent"
    assert result.about == "test agent about"
    assert result.metadata == {"test": "test"}


@test("ToolCallsEvaluator: test prepare_tool_call for agent.delete")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "agent.delete"
    arguments = {
        "developer_id": str(developer.id),
        "agent_id": str(agent.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, ResourceDeletedResponse)
    assert result.id == agent.id


@test("ToolCallsEvaluator: test prepare_tool_call for agent.list")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "agent.list"
    arguments = {
        "developer_id": str(developer.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, list)
    assert result[0].model == "gpt-4o-mini"
    assert result[0].name == "test agent"
    assert result[0].about == "test agent about"
    assert result[0].metadata == {"test": "test"}


@test("ToolCallsEvaluator: test prepare_tool_call for agent.doc.create")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "agent.doc.create"
    arguments = {
        "x_developer_id": str(developer.id),
        "agent_id": str(agent.id),
        "data": {
            "title": "Test Document",
            "content": "Test content",
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, Doc)
    assert result.title == "Test Document"
    assert result.content == ["Test content"]


@test("ToolCallsEvaluator: test prepare_tool_call for agent.doc.delete")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent, doc=test_doc):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "agent.doc.delete"
    arguments = {
        "developer_id": str(developer.id),
        "doc_id": str(doc.id),
        "owner_type": "agent",
        "owner_id": str(agent.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, ResourceDeletedResponse)
    assert result.id == doc.id


@test("ToolCallsEvaluator: test prepare_tool_call for agent.doc.list")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent, doc=test_doc):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "agent.doc.list"
    arguments = {
        "developer_id": str(developer.id),
        "owner_type": "agent",
        "owner_id": str(agent.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].id == doc.id


@skip("this needs to be fixed")
@test("ToolCallsEvaluator: test prepare_tool_call for agent.doc.search")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent, doc=test_doc):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "agent.doc.search"
    arguments = {
        "x_developer_id": str(developer.id),
        "agent_id": str(agent.id),
        "search_params": {
            "text": "test",
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, DocSearchResponse)
    assert len(result.docs) == 1
    assert result.docs[0].id == doc.id


@test("ToolCallsEvaluator: test prepare_tool_call for agent.doc.search, unknown search type")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent, doc=test_doc):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "agent.doc.search"
    arguments = {
        "x_developer_id": str(developer.id),
        "agent_id": str(agent.id),
        "search_params": {
            "unknown": "test",
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    with raises(ValueError) as exc:
        await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert str(exc.raised) == "Invalid search parameters"


@test("ToolCallsEvaluator: test prepare_tool_call for user.create")
async def _(dsn=pg_dsn, developer=test_developer):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "user.create"
    arguments = {
        "developer_id": str(developer.id),
        "data": {
            "name": "Test User",
            "about": "Test about",
            "metadata": {"key": "value"},
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, User)
    assert result.name == "Test User"
    assert result.about == "Test about"
    assert result.metadata == {"key": "value"}


@test("ToolCallsEvaluator: test prepare_tool_call for user.update")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "user.update"
    arguments = {
        "developer_id": str(developer.id),
        "user_id": str(user.id),
        "data": {
            "name": "Updated User",
            "about": "Updated about",
            "metadata": {"updated_key": "updated_value"},
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, User)
    assert result.name == "Updated User"
    assert result.about == "Updated about"
    assert result.metadata == {"updated_key": "updated_value"}


@test("ToolCallsEvaluator: test prepare_tool_call for user.get")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "user.get"
    arguments = {
        "developer_id": str(developer.id),
        "user_id": str(user.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, User)
    assert result.name == "test user"
    assert result.about == "test user about"


@test("ToolCallsEvaluator: test prepare_tool_call for user.delete")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "user.delete"
    arguments = {
        "developer_id": str(developer.id),
        "user_id": str(user.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, ResourceDeletedResponse)
    assert result.id == user.id


@test("ToolCallsEvaluator: test prepare_tool_call for user.list")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "user.list"
    arguments = {
        "developer_id": str(developer.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, list)
    # assert len(result) == 1
    assert result[0].name == "test user"
    assert result[0].about == "test user about"


@test("ToolCallsEvaluator: test prepare_tool_call for user.doc.create")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "user.doc.create"
    arguments = {
        "x_developer_id": str(developer.id),
        "user_id": str(user.id),
        "data": {
            "title": "Test User Document",
            "content": "Test user content",
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, Doc)
    assert result.title == "Test User Document"
    assert result.content == ["Test user content"]


@test("ToolCallsEvaluator: test prepare_tool_call for user.doc.delete")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user, doc=test_user_doc):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "user.doc.delete"
    arguments = {
        "developer_id": str(developer.id),
        "doc_id": str(doc.id),
        "owner_type": "user",
        "owner_id": str(user.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, ResourceDeletedResponse)
    assert result.id == doc.id


@test("ToolCallsEvaluator: test prepare_tool_call for user.doc.list")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user, doc=test_user_doc):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "user.doc.list"
    arguments = {
        "developer_id": str(developer.id),
        "owner_type": "user",
        "owner_id": str(user.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].id == doc.id


@skip("this needs to be fixed")
@test("ToolCallsEvaluator: test prepare_tool_call for user.doc.search")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user, doc=test_user_doc):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "user.doc.search"
    arguments = {
        "x_developer_id": str(developer.id),
        "user_id": str(user.id),
        "search_params": {
            "text": "test",
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, DocSearchResponse)
    assert len(result.docs) == 1
    assert result.docs[0].id == doc.id


@test("ToolCallsEvaluator: test prepare_tool_call for user.doc.search, unknown search type")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user, doc=test_user_doc):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "user.doc.search"
    arguments = {
        "x_developer_id": str(developer.id),
        "user_id": str(user.id),
        "search_params": {
            "unknown": "test",
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    with raises(ValueError) as exc:
        await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert str(exc.raised) == "Invalid search parameters"


@test("ToolCallsEvaluator: test prepare_tool_call for session.create")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "session.create"
    arguments = {
        "x_developer_id": str(developer.id),
        "agent_id": str(agent.id),
        "data": {
            "agents": [str(agent.id)],
            "situation": "test situation",
            "system_template": "test system template",
            "render_templates": True,
            "token_budget": 1000,
            "context_overflow": "truncate",
            "auto_run_tools": False,
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, Session)
    assert result.situation == "test situation"
    assert result.system_template == "test system template"
    assert result.render_templates is True
    assert result.token_budget == 1000
    assert result.context_overflow == "truncate"
    assert result.auto_run_tools is False


@test("ToolCallsEvaluator: test prepare_tool_call for session.update")
async def _(dsn=pg_dsn, developer=test_developer, session=test_session):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "session.update"
    arguments = {
        "developer_id": str(developer.id),
        "session_id": str(session.id),
        "data": {
            "metadata": {"updated": "metadata"},
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, Session)
    assert result.id == session.id
    assert result.metadata == {"updated": "metadata"}


@test("ToolCallsEvaluator: test prepare_tool_call for session.get")
async def _(dsn=pg_dsn, developer=test_developer, session=test_session):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "session.get"
    arguments = {
        "developer_id": str(developer.id),
        "session_id": str(session.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, Session)
    assert result.id == session.id
    assert result.metadata == {"test": "test"}


@test("ToolCallsEvaluator: test prepare_tool_call for session.list")
async def _(dsn=pg_dsn, developer=test_developer, session=test_session):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "session.list"
    arguments = {
        "developer_id": str(developer.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, list)
    assert result[0].id == session.id
    assert result[0].metadata == {"test": "test"}


@test("ToolCallsEvaluator: test prepare_tool_call for session.history")
async def _(dsn=pg_dsn, developer=test_developer, session=test_session):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "session.history"
    arguments = {
        "developer_id": str(developer.id),
        "session_id": str(session.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, History)


@test("ToolCallsEvaluator: test prepare_tool_call for task.list")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent, task=test_task):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "task.list"
    arguments = {
        "developer_id": str(developer.id),
        "agent_id": str(agent.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, list)
    assert len(result) >= 1
    assert all(t.id == task.id for t in result)


@test("ToolCallsEvaluator: test prepare_tool_call for task.get")
async def _(dsn=pg_dsn, developer=test_developer, task=test_task):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "task.get"
    arguments = {
        "developer_id": str(developer.id),
        "task_id": str(task.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert result.id == task.id
    assert result.name == task.name
    assert result.description == task.description
    assert result.metadata == task.metadata
    assert result.main == task.main


@test("ToolCallsEvaluator: test prepare_tool_call for task.create")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "task.create"
    arguments = {
        "developer_id": str(developer.id),
        "agent_id": str(agent.id),
        "data": {
            "name": "Test Task",
            "description": "Test task description",
            "metadata": {"key": "value"},
            "main": [{"evaluate": {"hi": "_"}}],
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert result.name == "Test Task"
    assert result.description == "Test task description"
    assert result.metadata == {"key": "value"}
    assert result.main == [EvaluateStep(kind_="evaluate", label=None, evaluate={"hi": "_"})]


@test("ToolCallsEvaluator: test prepare_tool_call for task.update")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent, task=test_task):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "task.update"
    arguments = {
        "developer_id": str(developer.id),
        "task_id": str(task.id),
        "agent_id": str(agent.id),
        "data": {
            "name": "Updated Task",
            "description": "Updated task description",
            "metadata": {"updated_key": "updated_value"},
            "main": [{"evaluate": {"hi": "_"}}],
        },
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert result.id == task.id
    assert result.name == "Updated Task"
    assert result.description == "Updated task description"
    assert result.metadata == {"updated_key": "updated_value"}
    assert result.main == [EvaluateStep(kind_="evaluate", label=None, evaluate={"hi": "_"})]


@test("ToolCallsEvaluator: test prepare_tool_call for task.delete")
async def _(dsn=pg_dsn, developer=test_developer, task=test_task):
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    tool_name = "task.delete"
    arguments = {
        "developer_id": str(developer.id),
        "task_id": str(task.id),
    }
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    result = await evaluator.prepare_tool_call(developer.id, tool_name, arguments)
    assert isinstance(result, ResourceDeletedResponse)
    assert result.id == task.id


@test("ToolCallsEvaluator: test prepare_tool_call with invalid tool name format")
async def _():
    evaluator = ToolCallsEvaluator(completion_func=AsyncMock())
    developer_id = uuid4()
    tool_name = "invalid"
    arguments = {"x_developer_id": str(developer_id)}
    with raises(NotImplementedError) as exc:
        await evaluator.prepare_tool_call(developer_id, tool_name, arguments)
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


@test("ToolCallsEvaluator: test _get_tool_result with ChatCompletionMessageToolCall")
async def _():
    # Setup
    mock_completion_func = AsyncMock()
    evaluator = ToolCallsEvaluator(completion_func=mock_completion_func)

    # Mock the prepare_tool_call method
    evaluator.prepare_tool_call = AsyncMock(return_value="tool response")

    tool = ChatCompletionMessageToolCall(
        id="tool-123",
        type="function",
        function=Function(name="test_tool", arguments='{"arg1": "value1"}'),
    )

    developer_id = uuid4()

    # Call the method
    result = await evaluator._get_tool_result(tool, developer_id)

    # Verify results
    assert result["tool_call_id"] == "tool-123"
    assert result["role"] == "tool"
    assert result["name"] == "test_tool"
    assert result["content"] == "tool response"


@test("ToolCallsEvaluator: test _get_tool_result with dictionary")
async def _():
    # Setup
    mock_completion_func = AsyncMock()
    evaluator = ToolCallsEvaluator(completion_func=mock_completion_func)

    # Mock the prepare_tool_call method
    evaluator.prepare_tool_call = AsyncMock(return_value="dict tool response")

    # Create a dictionary representation of a tool call
    tool_dict = {
        "id": "dict-tool-456",
        "type": "function",
        "function": {"name": "dict_tool", "arguments": '{"arg2": "value2", "arg3": 123}'},
    }

    developer_id = uuid4()

    # Call the method
    result = await evaluator._get_tool_result(tool_dict, developer_id)

    # Verify results
    assert result["tool_call_id"] == "dict-tool-456"
    assert result["role"] == "tool"
    assert result["name"] == "dict_tool"
    assert result["content"] == "dict tool response"


@test("ToolCallsEvaluator: test completion method with no tool calls")
async def _():
    response = ModelResponse(
        choices=[
            Choices(
                message=Message(
                    content="Simple response with no tool calls",
                    role="assistant"
                ),
                index=0,
            )
        ]
    )
    mock_completion_func = AsyncMock(return_value=response)
    evaluator = ToolCallsEvaluator(completion_func=mock_completion_func)
    developer_id = uuid4()
    
    # Call the method
    kwargs = {"stream": False}
    result = await evaluator.completion(developer_id, **kwargs)
    
    # Verify results
    assert result.choices[0].message.content == "Simple response with no tool calls"
    assert result.choices[0].message.role == "assistant"
    assert not result.choices[0].message.tool_calls
    
    # Verify the completion function was called with the correct arguments
    mock_completion_func.assert_called_once()
    assert "messages" not in kwargs
    assert result == response


@test("ToolCallsEvaluator: test completion method with tool calls")
async def _(dsn=pg_dsn, developer=test_developer):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
    arguments = {
        "developer_id": str(developer.id),
        "data": {
            "name": "Test Agent",
            "model": "gpt-4",
            "instructions": "Test instructions",
            "metadata": {"key": "value"},
        },
    }
    tool_call = ChatCompletionMessageToolCall(
        id="tool-123",
        type="function",
        function=Function(name="agent.create", arguments=json.dumps(arguments))
    )
    response = ModelResponse(
        choices=[
            Choices(
                message=Message(
                    content=None,
                    role="assistant",
                    tool_calls=[tool_call]
                ),
                index=0,
            )
        ]
    )
    mock_completion_func = AsyncMock(return_value=response)
    evaluator = ToolCallsEvaluator(completion_func=mock_completion_func)    
    messages = [{"role": "user", "content": "Use an agent.create tool"}]
    developer_id = uuid4()
    
    # Call the method
    kwargs = {"stream": False}
    result = await evaluator.completion(developer_id, **kwargs)
    
    # Verify results
    assert result.choices[0].message.role == "assistant"
    assert result.choices[0].message.tool_calls == [tool_call]
    
    # Verify the completion function was called with updated messages
    assert mock_completion_func.call_count == 2


# @test("ToolCallsEvaluator: test completion method with multiple tool calls")
# async def _():
#     # Setup
#     tool_calls = [
#         ChatCompletionMessageToolCall(
#             id="tool-123",
#             type="function",
#             function=Function(name="first_tool", arguments='{"arg1": "value1"}')
#         ),
#         ChatCompletionMessageToolCall(
#             id="tool-456",
#             type="function",
#             function=Function(name="second_tool", arguments='{"arg2": "value2"}')
#         )
#     ]
    
#     mock_completion_func = AsyncMock(return_value=ModelResponse(
#         choices=[
#             Choice(
#                 message=ChatCompletionMessage(
#                     content=None,
#                     role="assistant",
#                     tool_calls=tool_calls
#                 ),
#                 index=0,
#             )
#         ]
#     ))
    
#     evaluator = ToolCallsEvaluator(completion_func=mock_completion_func)
    
#     # Mock the _get_tool_result method to return different results for each tool
#     tool_results = [
#         {
#             "tool_call_id": "tool-123",
#             "role": "tool",
#             "name": "first_tool",
#             "content": "First tool result"
#         },
#         {
#             "tool_call_id": "tool-456",
#             "role": "tool",
#             "name": "second_tool",
#             "content": "Second tool result"
#         }
#     ]
    
#     evaluator._get_tool_result = AsyncMock(side_effect=tool_results)
    
#     messages = [{"role": "user", "content": "Use multiple tools"}]
#     developer_id = uuid4()
    
#     # Call the method
#     result = await evaluator.completion(developer_id, **{"messages": messages})
    
#     # Verify results
#     assert result.choices[0].message.role == "assistant"
#     assert result.choices[0].message.tool_calls == tool_calls
    
#     # Verify the tool results were added to messages
#     assert evaluator._get_tool_result.call_count == 2
    
#     # Verify the completion function was called with updated messages
#     assert mock_completion_func.call_count == 2
#     second_call_args = mock_completion_func.call_args[0][0]
#     assert len(second_call_args["messages"]) == 4  # Original + assistant + 2 tool results
#     assert second_call_args["messages"][2] == tool_results[0]
#     assert second_call_args["messages"][3] == tool_results[1]


# @test("ToolCallsEvaluator: test completion method with streaming and no tool calls")
# async def _():
#     # Setup
#     mock_stream_chunks = [
#         ModelResponseStream(
#             choices=[
#                 StreamChoice(
#                     delta=DeltaMessage(
#                         content="Streaming ",
#                         role="assistant",
#                     ),
#                     index=0,
#                 )
#             ]
#         ),
#         ModelResponseStream(
#             choices=[
#                 StreamChoice(
#                     delta=DeltaMessage(
#                         content="response ",
#                         role=None,
#                     ),
#                     index=0,
#                 )
#             ]
#         ),
#         ModelResponseStream(
#             choices=[
#                 StreamChoice(
#                     delta=DeltaMessage(
#                         content="with no tool calls",
#                         role=None,
#                     ),
#                     index=0,
#                 )
#             ]
#         ),
#     ]

#     async def mock_stream():
#         for chunk in mock_stream_chunks:
#             yield chunk

#     mock_completion_func = AsyncMock(return_value=mock_stream())
#     evaluator = ToolCallsEvaluator(completion_func=mock_completion_func)
    
#     messages = [{"role": "user", "content": "Hello"}]
#     developer_id = uuid4()
    
#     # Call the method
#     result = await evaluator.completion(developer_id, **{"messages": messages, "stream": True})
    
#     # Verify the completion function was called with the correct arguments
#     mock_completion_func.assert_called_once()
#     call_args = mock_completion_func.call_args[0][0]
#     assert call_args["messages"] == messages
#     assert call_args["stream"] is True
    
#     # Verify we get back the stream
#     chunks = []
#     async for chunk in result:
#         chunks.append(chunk)
    
#     assert chunks == mock_stream_chunks


# @test("ToolCallsEvaluator: test completion method with streaming and tool calls")
# async def _():
#     # Setup - create stream chunks that include tool calls
#     first_chunk = ModelResponseStream(
#         choices=[
#             StreamChoice(
#                 delta=DeltaMessage(
#                     content=None,
#                     role="assistant",
#                     tool_calls=[
#                         ToolCall(
#                             index=0,
#                             id="tool-123",
#                             function=ToolFunction(name="test_tool", arguments=""),
#                         )
#                     ],
#                 ),
#                 index=0,
#             )
#         ]
#     )
    
#     argument_chunks = [
#         ModelResponseStream(
#             choices=[
#                 StreamChoice(
#                     delta=DeltaMessage(
#                         tool_calls=[
#                             ToolCall(
#                                 index=0,
#                                 function=ToolFunction(arguments='{"arg'),
#                             )
#                         ],
#                     ),
#                     index=0,
#                 )
#             ]
#         ),
#         ModelResponseStream(
#             choices=[
#                 StreamChoice(
#                     delta=DeltaMessage(
#                         tool_calls=[
#                             ToolCall(
#                                 index=0,
#                                 function=ToolFunction(arguments='1": "value1"}'),
#                             )
#                         ],
#                     ),
#                     index=0,
#                 )
#             ]
#         ),
#     ]
    
#     # Mock the stream generator
#     async def mock_stream():
#         yield first_chunk
#         for chunk in argument_chunks:
#             yield chunk

#     mock_completion_func = AsyncMock(return_value=mock_stream())
#     evaluator = ToolCallsEvaluator(completion_func=mock_completion_func)
    
#     # Mock the tool result
#     tool_result = {
#         "tool_call_id": "tool-123",
#         "role": "tool",
#         "name": "test_tool",
#         "content": "Tool execution result"
#     }
#     evaluator._get_tool_result = AsyncMock(return_value=tool_result)
    
#     # Mock the second completion after tool execution
#     second_response_chunks = [
#         ModelResponseStream(
#             choices=[
#                 StreamChoice(
#                     delta=DeltaMessage(
#                         content="Final ",
#                         role="assistant",
#                     ),
#                     index=0,
#                 )
#             ]
#         ),
#         ModelResponseStream(
#             choices=[
#                 StreamChoice(
#                     delta=DeltaMessage(
#                         content="response",
#                         role=None,
#                     ),
#                     index=0,
#                 )
#             ]
#         ),
#     ]
    
#     async def mock_second_stream():
#         for chunk in second_response_chunks:
#             yield chunk
    
#     # Set up the mock to return different values on subsequent calls
#     mock_completion_func.side_effect = [mock_stream(), mock_second_stream()]
    
#     messages = [{"role": "user", "content": "Use a tool"}]
#     developer_id = uuid4()
    
#     # Call the method
#     result = await evaluator.completion(developer_id, **{"messages": messages, "stream": True})
    
#     # Verify the completion function was called twice
#     assert mock_completion_func.call_count == 2
    
#     # Verify the first call had the original messages
#     first_call_args = mock_completion_func.call_args_list[0][0][0]
#     assert first_call_args["messages"] == messages
#     assert first_call_args["stream"] is True
    
#     # Verify the second call included the tool result
#     second_call_args = mock_completion_func.call_args_list[1][0][0]
#     assert len(second_call_args["messages"]) == 3  # Original + assistant + tool result
#     assert second_call_args["messages"][2] == tool_result
    
#     # Verify we get back the second stream
#     chunks = []
#     async for chunk in result:
#         chunks.append(chunk)
    
#     assert chunks == second_response_chunks
