# # Tests for entry queries
# from uuid import uuid4

# from cozo_migrate.api import init, apply
# from pycozo import Client
# from ward import test


# from .create_docs import create_docs_query
# from .delete_docs import delete_docs_by_id_query
# from .get_docs import get_docs_snippets_by_id_query
# from .list_docs import list_docs_snippets_by_owner_query
# from .embed_docs import embed_docs_snippets_query
# from .search_docs import search_docs_snippets_by_embedding_query


# EMBEDDING_SIZE: int = 1024


# def cozo_client(migrations_dir: str = "./migrations"):
#     # Create a new client for each test
#     # and initialize the schema.
#     client = Client()

#     init(client)
#     apply(client, migrations_dir=migrations_dir, all_=True)

#     return client


# @test("model: create docs")
# def _():
#     client = cozo_client()

#     for owner_type in ("user", "agent"):
#         owner_id = uuid4()
#         id = uuid4()

#         result = create_docs_query(
#             owner_type, owner_id, id, title="Hello", content="World", client=client
#         )

#         assert result["created_at"][0]


# @test("model: get docs")
# def _():
#     client = cozo_client()

#     for owner_type in ("user", "agent"):
#         owner_id = uuid4()
#         id = uuid4()

#         create_docs_query(
#             owner_type, owner_id, id, title="Hello", content="World", client=client
#         )

#         result = get_docs_snippets_by_id_query(owner_type, id, client=client)

#         assert len(result) == 1, "Only 1 should have been found"


# @test("model: delete docs")
# def _():
#     client = cozo_client()

#     for owner_type in ("user", "agent"):
#         owner_id = uuid4()
#         id = uuid4()

#         create_docs_query(
#             owner_type, owner_id, id, title="Hello", content="World", client=client
#         )

#         result = delete_docs_by_id_query(owner_type, owner_id, id, client=client)

#         delete_info = next(
#             (row for row in result.to_dict("records") if row["_kind"] == "deleted"),
#             None,
#         )

#         assert delete_info is not None, "Delete operation found the row"


# @test("model: list docs")
# def _():
#     client = cozo_client()

#     for owner_type in ("user", "agent"):
#         owner_id = uuid4()
#         id = uuid4()

#         create_docs_query(
#             owner_type, owner_id, id, title="Hello", content="World", client=client
#         )

#         result = list_docs_snippets_by_owner_query(owner_type, owner_id, client=client)

#         assert len(result) == 1, "Only 1 should have been found"


# @test("model: search docs")
# def _():
#     client = cozo_client()

#     for owner_type in ("user", "agent"):
#         owner_id = uuid4()
#         id = uuid4()

#         create_docs_query(
#             owner_type, owner_id, id, title="Hello", content="World", client=client
#         )

#         ### Add embedding to the snippet
#         client.update(
#             "information_snippets",
#             dict(doc_id=str(id), snippet_idx=0, embedding=[1.0] * EMBEDDING_SIZE),
#         )

#         ### Search
#         query_embedding = [0.99] * EMBEDDING_SIZE

#         result = search_docs_snippets_by_embedding_query(
#             owner_type, owner_id, query_embedding, client=client
#         )

#         assert len(result) == 1, "Only 1 should have been found"


# @test("model: embed docs")
# def _():
#     client = cozo_client()

#     for owner_type in ("user", "agent"):
#         owner_id = uuid4()
#         id = uuid4()

#         snippets = [
#             "Hello World",
#             "Hello Banana",
#             "Hello Apple",
#         ]

#         create_docs_query(
#             owner_type,
#             owner_id,
#             id,
#             title="Hi",
#             content=snippets,
#             client=client,
#         )

#         ### Add embedding to the snippet
#         snippet_indices = [*range(len(snippets))]

#         embeddings = [[1.0] * EMBEDDING_SIZE for _ in snippets]

#         embed_docs_snippets_query(id, snippet_indices, embeddings, client=client)
