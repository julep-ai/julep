import json
from typing import Any
from uuid import UUID

from beartype import beartype
from pydantic import AnyUrl, BaseModel
from temporalio import activity

from ..app import app
from ..autogen.openapi_model import BaseIntegrationDef
from ..clients import integrations
from ..common.exceptions.tools import IntegrationExecutionException
from ..env import testing
from ..queries import tools


def serialize_pydantic_objects(obj: Any) -> Any:
    """Recursively convert Pydantic types to JSON-serializable formats."""
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, AnyUrl):
        return str(obj)
    if isinstance(obj, dict):
        return {k: serialize_pydantic_objects(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_pydantic_objects(item) for item in obj]
    return obj


@beartype
async def execute_integration(
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID | None,
    session_id: UUID | None,
    tool_name: str,
    integration: BaseIntegrationDef,
    arguments: dict[str, Any],
    setup: dict[str, Any] = {},
    connection_pool=None,
) -> Any:
    # AIDEV-NOTE: task_id or session_id must be provided (one for task execution, one for chat)
    if task_id is None and session_id is None:
        msg = "Either task_id or session_id must be provided"
        raise ValueError(msg)

    if connection_pool is None:
        connection_pool = getattr(app.state, "postgres_pool", None)

    merged_tool_args = await tools.get_tool_args_from_metadata(
        developer_id=developer_id,
        agent_id=agent_id,
        task_id=task_id,
        session_id=session_id,
        arg_type="args",
        connection_pool=connection_pool,
    )

    merged_tool_setup = await tools.get_tool_args_from_metadata(
        developer_id=developer_id,
        agent_id=agent_id,
        task_id=task_id,
        session_id=session_id,
        arg_type="setup",
        connection_pool=connection_pool,
    )

    arguments = arguments | (integration.arguments or {}) | merged_tool_args.get(tool_name, {})

    # Convert integration.setup to dict and ensure all Pydantic types are serialized
    integration_setup = {}
    if integration.setup:
        # Use our helper to recursively serialize any Pydantic objects
        integration_setup = serialize_pydantic_objects(integration.setup)

    # Serialize both setup and arguments to ensure no Pydantic objects remain
    setup = serialize_pydantic_objects(
        setup | integration_setup | merged_tool_setup.get(tool_name, {})
    )
    arguments = serialize_pydantic_objects(arguments)

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
