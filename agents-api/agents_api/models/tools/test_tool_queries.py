# # Tests for entry queries
# from uuid import uuid4

# from cozo_migrate.api import init, apply
# from pycozo import Client
# from ward import test

# from ...autogen.openapi_model import FunctionDef
# from .create_tools import create_function_query, create_multiple_functions_query
# from .delete_tools import delete_function_by_id_query
# from .get_tool import get_function_by_id_query
# from .list_tools import list_functions_by_agent_query


# def cozo_client(migrations_dir: str = "./migrations"):
#     # Create a new client for each test
#     # and initialize the schema.
#     client = Client()

#     init(client)
#     apply(client, migrations_dir=migrations_dir, all_=True)

#     return client


# @test("model: create function")
# def _():
#     client = cozo_client()

#     agent_id = uuid4()
#     tool_id = uuid4()
#     function = FunctionDef(
#         name="hello_world",
#         description="A function that prints hello world",
#         parameters={"type": "object", "properties": {}},
#     )

#     result = create_function_query(agent_id, tool_id, function, client=client)

#     assert result["created_at"][0]


# @test("model: create multiple functions")
# def _():
#     client = cozo_client()

#     agent_id = uuid4()
#     function = FunctionDef(
#         name="hello_world",
#         description="A function that prints hello world",
#         parameters={"type": "object", "properties": {}},
#     )
#     num_functions = 10

#     result = create_multiple_functions_query(
#         agent_id, [function] * num_functions, client=client
#     )

#     assert result["created_at"][0]
#     assert len(result["tool_id"]) == num_functions


# @test("model: delete function")
# def _():
#     client = cozo_client()

#     # Create function
#     agent_id = uuid4()
#     tool_id = uuid4()
#     function = FunctionDef(
#         name="hello_world",
#         description="A function that prints hello world",
#         parameters={"type": "object", "properties": {}},
#     )

#     create_function_query(agent_id, tool_id, function, client=client)

#     # Delete function
#     result = delete_function_by_id_query(agent_id, tool_id, client=client)

#     delete_info = next(
#         (row for row in result.to_dict("records") if row["_kind"] == "deleted"), None
#     )

#     assert delete_info is not None, "Delete operation did not find the row"


# @test("model: get function")
# def _():
#     client = cozo_client()

#     # Create function
#     agent_id = uuid4()
#     tool_id = uuid4()
#     function = FunctionDef(
#         name="hello_world",
#         description="A function that prints hello world",
#         parameters={"type": "object", "properties": {}},
#     )

#     create_function_query(agent_id, tool_id, function, client=client)

#     # Get function
#     result = get_function_by_id_query(agent_id, tool_id, client=client)

#     assert len(result["tool_id"]) == 1, "Get operation did not find the row"


# @test("model: list functions")
# def _():
#     client = cozo_client()

#     agent_id = uuid4()
#     function = FunctionDef(
#         name="hello_world",
#         description="A function that prints hello world",
#         parameters={"type": "object", "properties": {}},
#     )
#     num_functions = 10

#     # Create functions
#     create_multiple_functions_query(agent_id, [function] * num_functions, client=client)

#     # List functions
#     result = list_functions_by_agent_query(agent_id, client=client)

#     assert len(result["tool_id"]) == num_functions
