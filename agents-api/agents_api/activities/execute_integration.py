from typing import Any

from beartype import beartype
from temporalio import activity

from ..autogen.openapi_model import IntegrationDef
from ..clients import integrations
from ..common.protocol.tasks import StepContext
from ..env import testing
from ..models.tools import get_tool_args_from_metadata


@beartype
async def execute_integration(
    context: StepContext,
    tool_name: str,
    integration: IntegrationDef,
    arguments: dict[str, Any],
    setup: dict[str, Any] = {},
) -> Any:
    developer_id = context.execution_input.developer_id
    agent_id = context.execution_input.agent.id
    task_id = context.execution_input.task.id

    merged_tool_args = get_tool_args_from_metadata(
        developer_id=developer_id, agent_id=agent_id, task_id=task_id, arg_type="args"
    )

    merged_tool_setup = get_tool_args_from_metadata(
        developer_id=developer_id, agent_id=agent_id, task_id=task_id, arg_type="setup"
    )

    arguments = (
        merged_tool_args.get(tool_name, {}) | (integration.arguments or {}) | arguments
    )

    setup = merged_tool_setup.get(tool_name, {}) | (integration.setup or {}) | setup

    try:
        if integration.provider == "dummy":
            return arguments

        return await integrations.run_integration_service(
            provider=integration.provider,
            setup=setup,
            method=integration.method,
            arguments=arguments,
        )

    except BaseException as e:
        if activity.in_activity():
            activity.logger.error(f"Error in execute_integration: {e}")

        raise


mock_execute_integration = execute_integration

execute_integration = activity.defn(name="execute_integration")(
    execute_integration if not testing else mock_execute_integration
)
