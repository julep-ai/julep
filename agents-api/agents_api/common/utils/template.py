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
async def render_template(
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
