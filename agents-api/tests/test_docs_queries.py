# Tests for entry queries

from ward import test

from agents_api.autogen.openapi_model import CreateDocRequest
from agents_api.models.docs.create_doc import create_doc
from agents_api.models.docs.delete_doc import delete_doc
from agents_api.models.docs.embed_snippets import embed_snippets
from agents_api.models.docs.get_doc import get_doc
from agents_api.models.docs.list_docs import list_docs
from agents_api.models.docs.search_docs_by_embedding import search_docs_by_embedding
from tests.fixtures import (
    cozo_client,
    test_agent,
    test_developer_id,
    test_doc,
    test_user,
)

EMBEDDING_SIZE: int = 1024


@test("model: create docs")
def _(
    client=cozo_client, developer_id=test_developer_id, agent=test_agent, user=test_user
):
    create_doc(
        developer_id=developer_id,
        owner_type="agent",
        owner_id=agent.id,
        data=CreateDocRequest(title="Hello", content=["World"]),
        client=client,
    )

    create_doc(
        developer_id=developer_id,
        owner_type="user",
        owner_id=user.id,
        data=CreateDocRequest(title="Hello", content=["World"]),
        client=client,
    )


@test("model: get docs")
def _(client=cozo_client, doc=test_doc, developer_id=test_developer_id):
    get_doc(
        developer_id=developer_id,
        doc_id=doc.id,
        client=client,
    )


@test("model: delete doc")
def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
    doc = create_doc(
        developer_id=developer_id,
        owner_type="agent",
        owner_id=agent.id,
        data=CreateDocRequest(title="Hello", content=["World"]),
        client=client,
    )

    delete_doc(
        developer_id=developer_id,
        doc_id=doc.id,
        owner_type="agent",
        owner_id=agent.id,
        client=client,
    )


@test("model: list docs")
def _(
    client=cozo_client, developer_id=test_developer_id, doc=test_doc, agent=test_agent
):
    result = list_docs(
        developer_id=developer_id,
        owner_type="agent",
        owner_id=agent.id,
        client=client,
    )

    assert len(result) >= 1


@test("model: search docs")
def _(client=cozo_client, agent=test_agent, developer_id=test_developer_id):
    doc = create_doc(
        developer_id=developer_id,
        owner_type="agent",
        owner_id=agent.id,
        data=CreateDocRequest(title="Hello", content=["World"]),
        client=client,
    )

    ### Add embedding to the snippet
    embed_snippets(
        developer_id=developer_id,
        doc_id=doc.id,
        snippet_indices=[0],
        embeddings=[[1.0] * EMBEDDING_SIZE],
        client=client,
    )

    ### Search
    query_embedding = [0.99] * EMBEDDING_SIZE

    result = search_docs_by_embedding(
        developer_id=developer_id,
        owner_type="agent",
        owner_id=agent.id,
        query_embedding=query_embedding,
        client=client,
    )

    assert len(result) >= 1


@test("model: embed snippets")
def _(client=cozo_client, developer_id=test_developer_id, doc=test_doc):
    snippet_indices = [0]
    embeddings = [[1.0] * EMBEDDING_SIZE]

    result = embed_snippets(
        developer_id=developer_id,
        doc_id=doc.id,
        snippet_indices=snippet_indices,
        embeddings=embeddings,
        client=client,
    )

    assert result is not None
    assert result.id == doc.id
