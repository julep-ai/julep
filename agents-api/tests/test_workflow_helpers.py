import uuid
from unittest.mock import patch

from agents_api.autogen.openapi_model import (
    Agent,
    MapReduceStep,
    PromptItem,
    PromptStep,
    TaskSpecDef,
    TransitionTarget,
    Workflow,
    YieldStep,
)
from agents_api.common.protocol.tasks import (
    ExecutionInput,
    StepContext,
)
from agents_api.common.utils.datetime import utcnow
from agents_api.workflows.task_execution.helpers import execute_map_reduce_step_parallel
from ward import raises, test


# @test("execute_map_reduce_step_parallel: subworkflow step not supported")
# async def _():
#     async def _resp():
#         return "response"

#     subworkflow_step = YieldStep(
#         kind_="yield", workflow="subworkflow", arguments={"test": "$ _"}
#     )

#     step = MapReduceStep(
#         kind_="map_reduce",
#         map=subworkflow_step,
#         over="$ [1, 2, 3]",
#         parallelism=3,
#     )

#     execution_input = ExecutionInput(
#         developer_id=uuid.uuid4(),
#         agent=Agent(
#             id=uuid.uuid4(), name="test agent", created_at=utcnow(), updated_at=utcnow()
#         ),
#         agent_tools=[],
#         arguments={},
#         task=TaskSpecDef(
#             name="task1",
#             tools=[],
#             workflows=[Workflow(name="main", steps=[step])],
#         ),
#     )

#     context = StepContext(
#         execution_input=execution_input,
#         current_input={"current_input": "value 1"},
#         cursor=TransitionTarget(
#             workflow="main",
#             step=0,
#         ),
#     )
#     with patch("agents_api.workflows.task_execution.helpers.workflow") as workflow:
#         workflow.execute_activity.return_value = await _resp()
#         with raises(ValueError):
#             await execute_map_reduce_step_parallel(
#                 context=context,
#                 map_defn=step.map,
#                 execution_input=execution_input,
#                 items=["1", "2", "3"],
#                 current_input={},
#             )


@test("execute_map_reduce_step_parallel: parallelism must be greater than 1")
async def _():
    async def _resp():
        return "response"

    subworkflow_step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])

    step = MapReduceStep(
        kind_="map_reduce",
        map=subworkflow_step,
        over="$ [1, 2, 3]",
        parallelism=1,
    )

    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(), name="test agent", created_at=utcnow(), updated_at=utcnow()
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )

    context = StepContext(
        execution_input=execution_input,
        current_input={"current_input": "value 1"},
        cursor=TransitionTarget(
            workflow="main",
            step=0,
        ),
    )
    with patch("agents_api.workflows.task_execution.helpers.workflow") as workflow:
        workflow.execute_activity.return_value = await _resp()
        with raises(AssertionError):
            await execute_map_reduce_step_parallel(
                context=context,
                map_defn=step.map,
                execution_input=execution_input,
                items=["1", "2", "3"],
                current_input={},
                parallelism=1,
            )
