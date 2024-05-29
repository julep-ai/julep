import arrow
from jinja2.sandbox import ImmutableSandboxedEnvironment
from jinja2schema import infer, to_json_schema
from jsonschema import validate

__all__ = [
    "render_template",
]

# jinja environment
jinja_env = ImmutableSandboxedEnvironment(
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    auto_reload=False,
    enable_async=True,
    loader=None,
)

# Add arrow to jinja
jinja_env.globals["arrow"] = arrow


# Funcs
async def render_template_string(
    template_string: str, variables: dict, check: bool = False
) -> str:
    # Parse template
    template = jinja_env.from_string(template_string)

    # If check is required, get required vars from template and validate variables
    if check:
        schema = to_json_schema(infer(template_string))
        validate(instance=variables, schema=schema)

    # Render
    rendered = await template.render_async(**variables)
    return rendered


async def render_template_parts(
    template_strings: list[dict], variables: dict, check: bool = False
) -> list[dict]:
    # Parse template
    templates = [
        (jinja_env.from_string(msg["text"]) if msg["type"] == "text" else None)
        for msg in template_strings
    ]

    # If check is required, get required vars from template and validate variables
    if check:
        for template in templates:
            if template is None:
                continue

            schema = to_json_schema(infer(template))
            validate(instance=variables, schema=schema)

    # Render
    rendered = [
        (
            {"type": "text", "text": await template.render_async(**variables)}
            if template is not None
            else msg
        )
        for template, msg in zip(templates, template_strings)
    ]

    return rendered


async def render_template(
    template_string: str | list[dict], variables: dict, check: bool = False
) -> str | list[dict]:
    if isinstance(template_string, str):
        return await render_template_string(template_string, variables, check)

    elif isinstance(template_string, list):
        return await render_template_parts(template_string, variables, check)

    else:
        raise ValueError("template_string should be str or list[dict]")
