import importlib

from beartype import beartype
from fastapi import HTTPException

from .. import providers as available_providers
from ..models.base_models import BaseProvider, IdentifierName
from ..models.execution import (
    ExecutionArguments,
    ExecutionError,
    ExecutionResponse,
    ExecutionSetup,
)


@beartype
async def execute_integration(
    *,
    provider: IdentifierName,
    method: IdentifierName | None = None,
    setup: ExecutionSetup | None = None,
    arguments: ExecutionArguments,
) -> ExecutionResponse:
    provider_obj = getattr(available_providers, provider, None)
    if not provider_obj or not isinstance(provider_obj, BaseProvider):
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    method = method or provider_obj.methods[0].method
    method_config = next((m for m in provider_obj.methods if m.method == method), None)
    if not method_config:
        raise HTTPException(
            status_code=400, detail=f"Unknown method: {method} for provider: {provider}"
        )

    provider_module = importlib.import_module(
        f"integrations.utils.integrations.{provider_obj.provider}",
        package="integrations",
    )

    if (
        setup is not None
        and provider_obj.setup
        and not isinstance(setup, provider_obj.setup)
    ):
        setup = provider_obj.setup(**setup.model_dump())

    arguments = (
        method_config.arguments(**arguments.model_dump())
        if not isinstance(arguments, method_config.arguments)
        else arguments
    )

    try:
        return await getattr(provider_module, method)(
            **({"setup": setup} if setup else {}), arguments=arguments
        )
    except BaseException as e:
        return ExecutionError(error=str(e))
