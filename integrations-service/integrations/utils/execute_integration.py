import importlib

from ..models.base_models import BaseProvider, IdentifierName
from ..models.execution import ExecutionArguments, ExecutionResponse, ExecutionSetup
from ..providers import providers


async def execute_integration(
    provider: IdentifierName,
    arguments: ExecutionArguments,
    method: IdentifierName | None = None,
    setup: ExecutionSetup | None = None,
) -> ExecutionResponse:
    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}")
    provider: BaseProvider = providers[provider]
    if method is None:
        method = provider.methods[0].method
    if method not in [method.method for method in provider.methods]:
        raise ValueError(f"Unknown method: {method} for provider: {provider}")

    provider_module = importlib.import_module(
        f"integrations.utils.integrations.{provider.provider}", package="integrations"
    )
    execution_function = getattr(provider_module, method)

    if setup:
        setup_class = provider.setup
        if setup_class and not isinstance(setup, setup_class):
            setup = setup_class(**setup.model_dump())

    arguments_class = next(m for m in provider.methods if m.method == method).arguments

    if not isinstance(arguments, arguments_class):
        parsed_arguments = arguments_class(**arguments.model_dump())
    else:
        parsed_arguments = arguments

    if setup:
        return await execution_function(setup=setup, arguments=parsed_arguments)
    else:
        return execution_function(arguments=parsed_arguments)
