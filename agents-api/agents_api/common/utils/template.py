from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException, status
from jinja2 import TemplateSyntaxError, UndefinedError
from jinja2.sandbox import ImmutableSandboxedEnvironment
from jinja2schema import infer, to_json_schema
from jsonschema import validate
from psycopg import AsyncConnection

from ...activities.utils import ALLOWED_FUNCTIONS, constants, stdlib
from ...queries.secrets import get_secret_by_name

__all__: list[str] = [
    "get_secrets",
    "render_template",
]

# jinja environment
jinja_env: ImmutableSandboxedEnvironment = ImmutableSandboxedEnvironment(
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    auto_reload=False,
    enable_async=True,
    loader=None,
)

# Add constants and stdlib functions to jinja
for k, v in (constants | stdlib | ALLOWED_FUNCTIONS).items():
    jinja_env.globals[k] = v


# Function to get secrets for templates
async def get_secrets(
    conn: AsyncConnection[dict[str, Any]],
    developer_id: UUID,
    agent_id: UUID | None,
    secret_refs: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """
    Get secrets for template rendering.

    Args:
        conn: Database connection.
        developer_id: Developer ID.
        agent_id: Optional agent ID.
        secret_refs: Dictionary of secret references with format {variable_name: {"name": "secret_name"}}.

    Returns:
        Dictionary of resolved secrets with format {variable_name: secret_value}.
    """
    secrets = {}

    for var_name, ref in secret_refs.items():
        # Skip if the ref is not properly formatted
        if not isinstance(ref, dict) or "name" not in ref:
            continue

        secret_name = ref["name"]
        secret_result = await get_secret_by_name(
            conn=conn,
            name=secret_name,
            developer_id=developer_id,
            agent_id=agent_id,
        )

        if secret_result:
            # Secret found, store the value (hashed) in the secrets dictionary
            secrets[var_name] = secret_result[0]  # First item is the value

    return secrets


# Funcs
@beartype
async def render_template_string(
    template_string: str,
    variables: dict,
    check: bool = False,
) -> str:
    try:
        # Parse template
        template = jinja_env.from_string(template_string)

        # If check is required, get required vars from template and validate variables
        if check:
            schema = to_json_schema(infer(template_string))
            validate(instance=variables, schema=schema)

        # Render
        return await template.render_async(**variables)
    except TemplateSyntaxError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template syntax error: {e!s}",
        )
    except UndefinedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template undefined variable: {e!s}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template rendering error: {e!s}",
        )


# A render function that can render arbitrarily nested lists of dicts
# only render keys: content, text, image_url
# and only render values that are strings
T = TypeVar("T", str, dict, list[dict | list[dict]], None)


@beartype
async def render_template_nested[T: (str, dict, list[dict | list[dict]], None)](
    input: T,
    variables: dict,
    check: bool = False,
) -> T:
    match input:
        case str():
            return await render_template_string(input, variables, check)
        case dict():
            return {
                k: await render_template_nested(v, variables, check) for k, v in input.items()
            }
        case list():
            return [await render_template_nested(v, variables, check) for v in input]
        case _:
            return input


@beartype
async def render_template[T: str | list[dict]](
    input: T,
    variables: dict,
    check: bool = False,
    skip_vars: list[str] | None = None,
) -> T:
    variables = {
        name: val
        for name, val in variables.items()
        if not (skip_vars is not None and isinstance(name, str) and name in skip_vars)
    }

    return await render_template_nested(input, variables, check)
