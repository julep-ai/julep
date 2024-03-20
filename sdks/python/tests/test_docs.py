from ward import test

from julep.api.types import (
    Doc,
)

from .fixtures import (
    client,
    async_client,
    test_agent_doc,
    test_user_doc,
    setup_agent_async,
    setup_agent_doc_async,
    setup_user_async,
    setup_user_doc_async,
)


@test("agent docs.create")
def _(client=client, doc=test_agent_doc):
    agent, created_doc = doc
    try:
        assert isinstance(created_doc, Doc)
    finally:
        response = client.docs.delete(agent_id=agent.id, doc_id=created_doc.id)
        assert response is None


@test("user docs.create")
def _(client=client, doc=test_user_doc):
    user, created_doc = doc
    try:
        assert isinstance(created_doc, Doc)
    finally:
        response = client.docs.delete(user_id=user.id, doc_id=created_doc.id)
        assert response is None


@test("agent docs.get")
def _(client=client, doc=test_agent_doc):
    agent, created_doc = doc
    response = client.docs.list(agent_id=agent.id)
    try:
        assert len(response) > 0
        assert isinstance(response[0], Doc)
    finally:
        response = client.docs.delete(agent_id=agent.id, doc_id=created_doc.id)
        assert response is None


@test("user docs.get")
def _(client=client, doc=test_user_doc):
    user, created_doc = doc
    response = client.docs.list(user_id=user.id)

    try:
        assert len(response) > 0
        assert isinstance(response[0], Doc)
    finally:
        response = client.docs.delete(user_id=user.id, doc_id=created_doc.id)
        assert response is None


@test("async agent docs.get, agent docs.create, agent docs.delete")
async def _(client=async_client):
    agent = await setup_agent_async(client)
    doc = await setup_agent_doc_async(client, agent)

    assert isinstance(doc, Doc)
    assert doc.agent_id == agent.id

    try:
        response = await client.docs.list(agent_id=agent.id)
        assert len(response) > 0
        assert isinstance(response[0], Doc)
    finally:
        response = await client.docs.delete(agent_id=agent.id, doc_id=doc.id)
        assert response is None
        await client.agents.delete(agent_id=agent.id)


@test("async user docs.get, user docs.create, user docs.delete")
async def _(client=async_client):
    user = await setup_user_async(client)
    doc = await setup_user_doc_async(client, user)

    assert isinstance(doc, Doc)
    assert doc.user_id == user.id

    try:
        response = await client.docs.list(user_id=user.id)
        assert len(response) > 0
        assert isinstance(response[0], Doc)
    finally:
        response = await client.docs.delete(user_id=user.id, doc_id=doc.id)
        assert response is None
        await client.users.delete(user_id=user.id)
