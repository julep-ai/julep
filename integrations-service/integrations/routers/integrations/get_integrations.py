import importlib
import inspect
from typing import List

from ...models.models import IntegrationDef
from ...utils.integrations import (
    dalle_image_generator,
    duckduckgo_search,
    hacker_news,
    twitter,
    weather,
    wikipedia,
)
from .router import router


@router.get("/integrations", tags=["integrations"])
async def get_integrations() -> List[IntegrationDef]:
    integrations = [
        dalle_image_generator,
        duckduckgo_search,
        twitter,
        wikipedia,
        hacker_news,
        weather,
    ]
    integration_defs = []

    for integration in integrations:
        module = importlib.import_module(integration.__module__)
        function = getattr(module, integration.__name__)
        signature = inspect.signature(function)

        integration_def = IntegrationDef(
            provider=integration.__name__,
            method=None,  # TODO: Change when we integrate toolkits with multiple methods
            description=function.__doc__,
            arguments={
                param.name: str(param.annotation)
                for param in signature.parameters.values()
                if param.name != "parameters"
            },
        )
        integration_defs.append(integration_def)

    return integration_defs
