import base64
import secrets

from beartype import beartype
from temporalio import activity

from ...activities.task_steps import base_evaluate
from ...autogen.openapi_model import ToolCallStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)


def generate_call_id():
    # Generate 18 random bytes (which will result in 24 base64 characters)
    random_bytes = secrets.token_bytes(18)
    # Encode to base64 and remove padding
    base64_string = base64.urlsafe_b64encode(random_bytes).decode("ascii").rstrip("=")
    # Add the "call_" prefix
    return f"call_{base64_string}"


@activity.defn
@beartype
async def tool_call_step(context: StepContext) -> StepOutcome:
    assert isinstance(context.current_step, ToolCallStep)

    tool_type, tool_name = context.current_step.tool.split(".")
    arguments = await base_evaluate(
        context.current_step.arguments, context.model_dump()
    )

    tools = context.execution_input.tools

    assert tool_name in [tool.name for tool in tools], f"Tool {tool_name} not found"

    call_id = generate_call_id()

    tool_call = {
        tool_type: {
            "arguments": arguments,
            "name": tool_name,
        },
        "id": call_id,
        "type": tool_type,
    }

    return StepOutcome(output=tool_call)
