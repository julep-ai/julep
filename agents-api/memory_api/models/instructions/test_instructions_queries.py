from uuid import uuid4

from cozo_migrate.api import init, apply
from pycozo import Client
from ward import test

from ...autogen.openapi_model import Instruction
from .create_instructions import create_instructions_query
from .delete_instructions import delete_instructions_by_agent_query
from .list_instructions import list_instructions_query
from .search_instructions import search_instructions_query


def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("create instructions")
def _():
    client = cozo_client()
    agent_id = uuid4()
    num_instructions = 10
    instructions = [
        Instruction(
            content=f"Instruction {i}",
        )
        for i in range(num_instructions)
    ]

    query = create_instructions_query(agent_id, instructions)

    result = client.run(query)
    assert (
        len(result["instruction_idx"]) == num_instructions
    ), "All instructions should have been created"


@test("delete instructions")
def _():
    client = cozo_client()
    agent_id = uuid4()
    num_instructions = 10
    instructions = [
        Instruction(
            content=f"Instruction {i}",
        )
        for i in range(num_instructions)
    ]

    # Create the instructions
    query = create_instructions_query(agent_id, instructions)
    client.run(query)

    # Delete the instructions
    query = delete_instructions_by_agent_query(agent_id)
    result = client.run(query)
    delete_num = len(
        [row for row in result.to_dict("records") if row["_kind"] == "deleted"]
    )

    assert delete_num == num_instructions, "Delete operation found the row"


@test("list instructions empty for non-existent agent")
def _():
    client = cozo_client()
    agent_id = uuid4()

    query = list_instructions_query(agent_id)
    result = client.run(query)

    assert len(result) == 0, "List operation should not find any rows"


@test("list instructions")
def _():
    client = cozo_client()
    agent_id = uuid4()
    num_instructions = 10
    instructions = [
        Instruction(
            content=f"Instruction {i}",
        )
        for i in range(num_instructions)
    ]

    # Create the instructions
    create_query = create_instructions_query(agent_id, instructions)
    client.run(create_query)

    # List the instructions
    query = list_instructions_query(agent_id)
    result = client.run(query)

    assert len(result) == num_instructions, "List operation should find 10 rows"


@test("search instructions")
def _():
    client = cozo_client()

    agent_id = uuid4()
    instruction = Instruction(
        content="Instruction",
    )

    create_query = create_instructions_query(agent_id, [instruction])

    client.run(create_query)

    ### Add embedding to the snippet
    client.update(
        "agent_instructions",
        dict(instruction_idx=0, agent_id=str(agent_id), embedding=[1.0] * 768),
    )

    ### Search
    query_embedding = [0.99] * 768

    query = search_instructions_query(
        agent_id,
        query_embedding,
    )

    result = client.run(query)
    assert len(result) == 1, "Only 1 should have been found"
