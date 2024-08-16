from typing import Any

from beartype import beartype
from temporalio import activity

from agents_api.autogen.Executions import TransitionTarget

from ...autogen.openapi_model import (
    YieldStep,
)
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from .utils import simple_eval_dict


@activity.defn
@beartype
async def yield_step(context: StepContext[YieldStep]) -> StepOutcome[dict[str, Any]]:
    workflow = context.definition.workflow
    exprs = context.definition.arguments
    arguments = simple_eval_dict(exprs, values=context.model_dump())

    transition_target = TransitionTarget(
        workflow=workflow,
        step=0,
    )

    return StepOutcome(output=arguments, transition_to=("step", transition_target))
