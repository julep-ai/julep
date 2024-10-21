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

    # FEEDBACK[@Bhabuk10]: The use of the `|` operator to merge dictionaries is a great choice 
    # for readability. However, be mindful of Python version compatibility since `|` is only 
    # supported in Python 3.9 and above. If backward compatibility is a concern, you may want to 
    # consider an alternative merging strategy.

    arguments = (
        merged_tool_args.get(tool_name, {}) | (integration.arguments or {}) | arguments
    )

    setup = merged_tool_setup.get(tool_name, {}) | (integration.setup or {}) | setup

    try:
        if integration.provider == "dummy":
            return arguments

        # FEEDBACK[@Bhabuk10]: It's unclear from the code what the "dummy" provider is 
        # expected to do. Consider adding a comment explaining this scenario or, alternatively, 
        # refactor it into a separate function to improve readability and isolate this logic.
        
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
        # QUESTION[@Bhabuk10]: Why is `BaseException` being caught instead of more specific 
        # exceptions (e.g., `KeyError`, `TypeError`, or integration-specific exceptions)? 
        # It might be useful to catch more granular exceptions to allow for better error handling 
        # and debugging.

mock_execute_integration = execute_integration

execute_integration = activity.defn(name="execute_integration")(
    execute_integration if not testing else mock_execute_integration
)

# FEEDBACK[@Bhabuk10]: This structure to handle testing with `mock_execute_integration` is a 
# solid pattern. However, it may be beneficial to document how `mock_execute_integration` 
# is expected to behave compared to the actual `execute_integration`. This could help future 
# contributors understand the purpose and limitations of the mock.
