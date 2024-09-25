import importlib
import inspect
import os
from typing import Any, List

from pydantic import BaseModel

from ...models.models import IntegrationDef
from ...utils import integrations
from .router import router


def create_integration_def(module: Any) -> IntegrationDef:
    module_parts = module.__name__.split(".")
    if len(module_parts) > 4:  # Nested integration
        provider = module_parts[-2]
        method = module_parts[-1]
    else:  # Top-level integration
        provider = module_parts[-1]
        method = None

    # Find the first function in the module
    function_name = next(
        name
        for name, obj in inspect.getmembers(module)
        if inspect.isfunction(obj) and not name.startswith("_")
    )
    function = getattr(module, function_name)
    signature = inspect.signature(function)

    # Get the Pydantic model for the parameters
    params_model = next(iter(signature.parameters.values())).annotation

    # Check if the params_model is a Pydantic model
    if issubclass(params_model, BaseModel):
        arguments = {}
        for field_name, field in params_model.model_fields.items():
            field_type = field.annotation
            arguments[field_name] = {
                "type": field_type.__name__.lower(),
                "description": field.description,
            }
    else:
        # Fallback to a dictionary if it's not a Pydantic model
        arguments = {
            param.name: {"type": str(param.annotation.__name__).lower()}
            for param in signature.parameters.values()
            if param.name != "parameters"
        }

    return IntegrationDef(
        provider=provider,
        method=method,
        description=function.__doc__.strip() if function.__doc__ else None,
        arguments=arguments,
    )


@router.get("/integrations", tags=["integrations"])
async def get_integrations() -> List[IntegrationDef]:
    integration_defs = []
    integrations_dir = os.path.dirname(integrations.__file__)

    for item in os.listdir(integrations_dir):
        item_path = os.path.join(integrations_dir, item)

        if os.path.isdir(item_path):
            # This is a toolkit
            for file in os.listdir(item_path):
                if file.endswith(".py") and not file.startswith("__"):
                    module = importlib.import_module(
                        f"...utils.integrations.{item}.{file[:-3]}", package=__package__
                    )
                    integration_defs.append(create_integration_def(module))
        elif item.endswith(".py") and not item.startswith("__"):
            # This is a single-file tool
            module = importlib.import_module(
                f"...utils.integrations.{item[:-3]}", package=__package__
            )
            integration_defs.append(create_integration_def(module))

    return integration_defs
