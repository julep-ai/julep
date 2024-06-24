from temporalio import activity
from uuid import uuid4


from ...common.protocol.tasks import (
    StepContext,
    TransitionInfo,
)


from ...models.execution.create_execution_transition import (
    create_execution_transition_query,
)


@activity.defn
async def transition_step(
    context: StepContext,
    transition_info: TransitionInfo,
) -> dict:
    print("Running transition step")
    raise NotImplementedError()

    # Get transition info
    transition_data = transition_info.model_dump(by_alias=False)

    # Get task token if it's a waiting step
    if transition_info.type == "awaiting_input":
        task_token = activity.info().task_token
        transition_data["__task_token"] = task_token

    # Create transition
    create_execution_transition_query(
        developer_id=context.developer_id,
        execution_id=context.execution.id,
        transition_id=uuid4(),
        **transition_data,
    )

    # Raise if it's a waiting step
    if transition_info.type == "awaiting_input":
        activity.raise_complete_async()
