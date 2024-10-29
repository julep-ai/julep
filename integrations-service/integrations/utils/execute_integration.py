import importlib

from beartype import beartype
from fastapi import HTTPException

from .. import providers as available_providers
from ..autogen.Tools import BaseIntegrationDef
from ..models.base_models import BaseProvider, IdentifierName
from ..models.execution import ExecutionArguments, ExecutionResponse, ExecutionSetup


@beartype
async def execute_integration(
    *,
    provider: IdentifierName,
    method: IdentifierName | None = None,
    setup: ExecutionSetup | None = None,
    arguments: ExecutionArguments,
) -> ExecutionResponse:
    provider_obj: BaseProvider | None = getattr(available_providers, provider, None)

    if not provider_obj:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    assert isinstance(provider_obj, BaseProvider)

    if method is None:
        method = provider_obj.methods[0].method

    elif method not in [method.method for method in provider_obj.methods]:
        raise HTTPException(
            status_code=400, detail=f"Unknown method: {method} for provider: {provider}"
        )

    provider_module = importlib.import_module(
        f"integrations.utils.integrations.{provider_obj.provider}",
        package="integrations",
    )

    execution_function = getattr(provider_module, method)

    if setup is not None:
        setup_class = provider_obj.setup

        if setup_class and not isinstance(setup, setup_class):
            setup_obj = setup_class(**setup.model_dump())

    arguments_class = next(
        m for m in provider_obj.methods if m.method == method
    ).arguments

    if not isinstance(arguments, arguments_class):
        parsed_arguments = arguments_class(**arguments.model_dump())
    else:
        parsed_arguments = arguments

    if setup:
        return await execution_function(setup=setup_obj, arguments=parsed_arguments)
    else:
        return execution_function(arguments=parsed_arguments)
