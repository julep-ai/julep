from uuid import uuid4

from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import CreateTransitionRequest, Transition
from ...clients.cozo import get_cozo_client
from ...common.protocol.tasks import StepContext
from ...env import testing
from ...models.execution.create_execution_transition import create_execution_transition


@beartype
async def transition_step(
    context: StepContext,
    transition_info: CreateTransitionRequest,
) -> Transition:
    need_to_wait = transition_info.type == "wait"

    # Get task token if it's a waiting step
    if need_to_wait:
        task_token = activity.info().task_token
        transition_info.task_token = task_token

    # Create transition
    transition = create_execution_transition(
        developer_id=context.execution_input.developer_id,
        execution_id=context.execution_input.execution.id,
        task_id=context.execution_input.task.id,
        data=transition_info,
        update_execution_status=True,
    )

    return transition


mock_transition_step = transition_step

transition_step = activity.defn(name="transition_step")(
    transition_step if not testing else mock_transition_step
)
