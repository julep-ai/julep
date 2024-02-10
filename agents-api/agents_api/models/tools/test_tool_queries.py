# # Tests for entry queries
from uuid import uuid4

from cozo_migrate.api import init, apply
from pycozo import Client
from ward import test

from ...autogen.openapi_model import FunctionDef
from .create_tools import create_function_query, create_multiple_functions_query
from .delete_tools import delete_function_by_id_query
from .get_tools import get_function_by_id_query
from .list_tools import list_functions_by_agent_query
from .embed_tools import embed_functions_query
from .search_tools import search_functions_by_embedding_query


def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("create function")
def _():
    client = cozo_client()

    agent_id = uuid4()
    tool_id = uuid4()
    function = FunctionDef(
        name="hello_world",
        description="A function that prints hello world",
        parameters={"type": "object", "properties": {}},
    )

    query = create_function_query(agent_id, tool_id, function)

    result = client.run(query)
    assert result["created_at"][0]


@test("create multiple functions")
def _():
    client = cozo_client()

    agent_id = uuid4()
    function = FunctionDef(
        name="hello_world",
        description="A function that prints hello world",
        parameters={"type": "object", "properties": {}},
    )
    num_functions = 10

    query = create_multiple_functions_query(agent_id, [function] * num_functions)

    result = client.run(query)
    assert result["created_at"][0]
    assert len(result["tool_id"]) == num_functions


@test("delete function")
def _():
    client = cozo_client()

    # Create function
    agent_id = uuid4()
    tool_id = uuid4()
    function = FunctionDef(
        name="hello_world",
        description="A function that prints hello world",
        parameters={"type": "object", "properties": {}},
    )

    create_query = create_function_query(agent_id, tool_id, function)

    client.run(create_query)

    # Delete function
    query = delete_function_by_id_query(agent_id, tool_id)

    result = client.run(query)
    delete_info = next(
        (row for row in result.to_dict("records") if row["_kind"] == "deleted"), None
    )

    assert delete_info is not None, "Delete operation did not find the row"


@test("get function")
def _():
    client = cozo_client()

    # Create function
    agent_id = uuid4()
    tool_id = uuid4()
    function = FunctionDef(
        name="hello_world",
        description="A function that prints hello world",
        parameters={"type": "object", "properties": {}},
    )

    create_query = create_function_query(agent_id, tool_id, function)

    client.run(create_query)

    # Get function
    query = get_function_by_id_query(agent_id, tool_id)

    result = client.run(query)
    assert len(result["tool_id"]) == 1, "Get operation did not find the row"


@test("list functions")
def _():
    client = cozo_client()

    agent_id = uuid4()
    function = FunctionDef(
        name="hello_world",
        description="A function that prints hello world",
        parameters={"type": "object", "properties": {}},
    )
    num_functions = 10

    # Create functions
    create_query = create_multiple_functions_query(agent_id, [function] * num_functions)
    client.run(create_query)

    # List functions
    query = list_functions_by_agent_query(agent_id)
    result = client.run(query)

    assert len(result["tool_id"]) == num_functions


@test("embed functions")
def _():
    client = cozo_client()

    agent_id = uuid4()
    tool_id = uuid4()
    function = FunctionDef(
        name="hello_world",
        description="A function that prints hello world",
        parameters={"type": "object", "properties": {}},
    )

    # Create function
    create_query = create_function_query(agent_id, tool_id, function)
    client.run(create_query)

    # embed functions
    embedding = [1.0] * 768
    query = embed_functions_query(agent_id, [tool_id], [embedding])
    client.run(query)


@test("search functions")
def _():
    client = cozo_client()

    agent_id = uuid4()
    tool_id = uuid4()
    function = FunctionDef(
        name="hello_world",
        description="A function that prints hello world",
        parameters={"type": "object", "properties": {}},
    )

    # Create function
    create_query = create_function_query(agent_id, tool_id, function)
    client.run(create_query)

    # embed functions
    embedding = [1.0] * 768
    embed_query = embed_functions_query(agent_id, [tool_id], [embedding])
    client.run(embed_query)

    ### Search
    query_embedding = [0.99] * 768

    query = search_functions_by_embedding_query(
        agent_id,
        query_embedding,
    )

    result = client.run(query)
    assert len(result) == 1, "Only 1 should have been found"
