import json
from typing import Any

from beartype import beartype
from temporalio import activity

from ..app import app
from ..autogen.openapi_model import BaseIntegrationDef
from ..clients import integrations
from ..common.exceptions.tools import IntegrationExecutionException
from ..common.protocol.tasks import ExecutionInput, StepContext
from ..env import testing
from ..queries import tools


@beartype
async def execute_integration(
    context: StepContext,
    tool_name: str,
    integration: BaseIntegrationDef,
    arguments: dict[str, Any],
    setup: dict[str, Any] = {},
) -> Any:
    if not isinstance(context.execution_input, ExecutionInput):
        msg = "Expected ExecutionInput type for context.execution_input"
        raise TypeError(msg)

    developer_id = context.execution_input.developer_id
    agent_id = context.execution_input.agent.id

    if context.execution_input.task is None:
        msg = "Task cannot be None in execution_input"
        raise ValueError(msg)

    task_id = context.execution_input.task.id

    merged_tool_args = await tools.get_tool_args_from_metadata(
        developer_id=developer_id,
        agent_id=agent_id,
        task_id=task_id,
        arg_type="args",
        connection_pool=app.state.postgres_pool,
    )

    merged_tool_setup = await tools.get_tool_args_from_metadata(
        developer_id=developer_id,
        agent_id=agent_id,
        task_id=task_id,
        arg_type="setup",
        connection_pool=app.state.postgres_pool,
    )

    arguments = merged_tool_args.get(tool_name, {}) | (integration.arguments or {}) | arguments

    setup = merged_tool_setup.get(tool_name, {}) | (integration.setup or {}) | setup

    try:
        # Handle dummy provider as a special case
        if integration.provider == "dummy":
            return arguments

        # Call the integration service
        integration_service_response = await integrations.run_integration_service(
            provider=integration.provider,
            setup=setup,
            method=integration.method,
            arguments=arguments,
        )

        # Check for error in the response
        if error_message := integration_service_response.get("error"):
            integration_str = (
                f"{integration.provider}.{integration.method}"
                if integration.method
                else integration.provider
            )

            # Log the error with more context
            if activity.in_activity():
                activity.logger.error(
                    f"Integration {integration_str} returned error: {error_message}. "
                    f"Arguments: {json.dumps(arguments)[:200]}..."
                )

            # Raise a proper exception with details
            raise IntegrationExecutionException(
                integration=integration,
                error=error_message,
            )

        return integration_service_response

    except IntegrationExecutionException:
        # Re-raise our custom exceptions directly
        raise
    except Exception as e:
        # For all other exceptions, add context
        integration_str = integration.provider + (
            "." + integration.method if integration.method else ""
        )

        if activity.in_activity():
            activity.logger.error(
                f"Error executing integration {integration_str}: {e!s}. Tool: {tool_name}"
            )

        # Re-raise with better context
        raise IntegrationExecutionException(
            integration=integration,
            error=f"Failed to execute {integration_str}: {e!s}",
        ) from e


mock_execute_integration = execute_integration

execute_integration = activity.defn(name="execute_integration")(
    execute_integration if not testing else mock_execute_integration,
)
