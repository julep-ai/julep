# Tests for entry queries
from uuid import uuid4

from cozo_migrate.api import init, apply
from pycozo import Client
from ward import test

from .create_docs import create_docs_query
from .delete_docs import delete_docs_by_id_query
from .get_docs import get_docs_snippets_by_id_query
from .list_docs import list_docs_snippets_by_owner_query
from .embed_docs import embed_docs_snippets_query
from .search_docs import search_docs_snippets_by_embedding_query


def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("create docs")
def _():
    client = cozo_client()

    for owner_type in ("user", "agent"):
        owner_id = uuid4()
        id = uuid4()

        query = create_docs_query(
            owner_type, owner_id, id, title="Hello", content="World"
        )

        result = client.run(query)
        assert result["created_at"][0]


@test("get docs")
def _():
    client = cozo_client()

    for owner_type in ("user", "agent"):
        owner_id = uuid4()
        id = uuid4()

        create_query = create_docs_query(
            owner_type, owner_id, id, title="Hello", content="World"
        )

        client.run(create_query)

        query = get_docs_snippets_by_id_query(owner_type, id)

        result = client.run(query)
        assert len(result) == 1, "Only 1 should have been found"


@test("delete docs")
def _():
    client = cozo_client()

    for owner_type in ("user", "agent"):
        owner_id = uuid4()
        id = uuid4()

        create_query = create_docs_query(
            owner_type, owner_id, id, title="Hello", content="World"
        )

        client.run(create_query)

        query = delete_docs_by_id_query(owner_type, owner_id, id)

        result = client.run(query)
        delete_info = next(
            (row for row in result.to_dict("records") if row["_kind"] == "deleted"),
            None,
        )

        assert delete_info is not None, "Delete operation found the row"


@test("list docs")
def _():
    client = cozo_client()

    for owner_type in ("user", "agent"):
        owner_id = uuid4()
        id = uuid4()

        create_query = create_docs_query(
            owner_type, owner_id, id, title="Hello", content="World"
        )

        client.run(create_query)

        query = list_docs_snippets_by_owner_query(owner_type, owner_id)

        result = client.run(query)
        assert len(result) == 1, "Only 1 should have been found"


@test("search docs")
def _():
    client = cozo_client()

    for owner_type in ("user", "agent"):
        owner_id = uuid4()
        id = uuid4()

        create_query = create_docs_query(
            owner_type, owner_id, id, title="Hello", content="World"
        )

        client.run(create_query)

        ### Add embedding to the snippet
        client.update(
            "information_snippets",
            dict(doc_id=str(id), snippet_idx=0, embedding=[1.0] * 768),
        )

        ### Search
        query_embedding = [0.99] * 768

        query = search_docs_snippets_by_embedding_query(
            owner_type,
            owner_id,
            query_embedding,
        )

        result = client.run(query)
        assert len(result) == 1, "Only 1 should have been found"


@test("embed docs")
def _():
    client = cozo_client()

    for owner_type in ("user", "agent"):
        owner_id = uuid4()
        id = uuid4()

        snippets = [
            "Hello World",
            "Hello Banana",
            "Hello Apple",
        ]

        create_query = create_docs_query(
            owner_type,
            owner_id,
            id,
            title="Hi",
            content="\n\n".join(snippets),
            split_fn=lambda x: x.split("\n\n"),
        )

        client.run(create_query)

        ### Add embedding to the snippet
        snippet_indices = [*range(len(snippets))]

        embeddings = [[1.0] * 768 for _ in snippets]

        query = embed_docs_snippets_query(
            id,
            snippet_indices,
            embeddings,
        )

        client.run(query)
