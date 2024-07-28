# # Tests for task queries
# from uuid import uuid4

# from cozo_migrate.api import init, apply
# from pycozo import Client
# from ward import test

# from .create_task import create_task_query
# from .get_task import get_task_query
# from .list_tasks import list_tasks_query


# def cozo_client(migrations_dir: str = "./migrations"):
#     # Create a new client for each test
#     # and initialize the schema.
#     client = Client()

#     init(client)
#     apply(client, migrations_dir=migrations_dir, all_=True)

#     return client


# @test("model: create task")
# def _():
#     client = cozo_client()
#     developer_id = uuid4()
#     agent_id = uuid4()
#     task_id = uuid4()

#     create_task_query(
#         developer_id=developer_id,
#         agent_id=agent_id,
#         task_id=task_id,
#         name="test task",
#         description="test task about",
#         input_schema={"type": "object", "additionalProperties": True},
#         client=client,
#     )


# @test("model: list tasks")
# def _():
#     client = cozo_client()
#     developer_id = uuid4()
#     agent_id = uuid4()

#     result = list_tasks_query(
#         developer_id=developer_id,
#         agent_id=agent_id,
#         client=client,
#     )

#     assert len(result["id"]) == 0


# @test("model: get task exists")
# def _():
#     client = cozo_client()
#     developer_id = uuid4()
#     agent_id = uuid4()
#     task_id = uuid4()

#     create_task_query(
#         developer_id=developer_id,
#         agent_id=agent_id,
#         task_id=task_id,
#         name="test task",
#         description="test task about",
#         input_schema={"type": "object", "additionalProperties": True},
#         client=client,
#     )

#     result = get_task_query(
#         agent_id=agent_id, task_id=task_id, developer_id=developer_id, client=client
#     )

#     assert len(result["id"]) == 1


# # @test("model: delete task")
# # def _():
# #     TODO: Implement this test
# #     raise NotImplementedError


# # @test("model: update task")
# # def _():
# #     TODO: Implement this test
# #     raise NotImplementedError
