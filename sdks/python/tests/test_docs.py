from ward import test

from julep.api.types import (
    Doc,
)

from .fixtures import (
    client,
    async_client,
    test_agent_doc,
    test_user_doc,
)


@test("docs: agent docs.create")
def _(client=client, agent_doc=test_agent_doc):
    created_doc, agent = agent_doc
    assert isinstance(created_doc, Doc)


@test("docs: user docs.create")
def _(client=client, user_doc=test_user_doc):
    created_doc, user = user_doc
    assert isinstance(created_doc, Doc)


@test("docs: agent docs.get")
def _(client=client, agent_doc=test_agent_doc):
    _, agent = agent_doc
    docs = client.docs.list(agent_id=agent.id)
    assert len(docs) > 0
    assert isinstance(docs[0], Doc)


@test("docs: user docs.get")
def _(client=client, user_doc=test_user_doc):
    _, user = user_doc
    docs = client.docs.list(user_id=user.id)

    assert len(docs) > 0
    assert isinstance(docs[0], Doc)


@test("docs: async agent docs.get, agent docs.create, agent docs.delete")
async def _(client=async_client, agent_doc=test_agent_doc):
    doc, agent = agent_doc

    assert isinstance(doc, Doc)
    assert doc.agent_id == agent.id

    docs = await client.docs.list(agent_id=agent.id)
    assert len(docs) > 0
    assert isinstance(docs[0], Doc)


@test("docs: async user docs.get, user docs.create, user docs.delete")
async def _(client=async_client, user_doc=test_user_doc):
    doc, user = user_doc

    assert isinstance(doc, Doc)
    assert doc.user_id == user.id

    docs = await client.docs.list(user_id=user.id)
    assert len(docs) > 0
    assert isinstance(docs[0], Doc)
