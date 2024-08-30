import json
import re
from typing import List, TypeVar

import arrow
import re2
import yaml
from beartype import beartype
from jinja2.sandbox import ImmutableSandboxedEnvironment
from jinja2schema import infer, to_json_schema
from jsonschema import validate

__all__: List[str] = [
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

# Add arrow to jinja

jinja_env.globals["dump_yaml"] = yaml.dump
jinja_env.globals["match_regex"] = lambda pattern, string: bool(
    re2.fullmatch(pattern, string)
)
jinja_env.globals["search_regex"] = lambda pattern, string: re2.search(pattern, string)
jinja_env.globals["dump_json"] = json.dumps
jinja_env.globals["arrow"] = arrow
jinja_env.globals["true"] = True
jinja_env.globals["false"] = False
jinja_env.globals["null"] = None


simple_jinja_regex = re.compile(r"{{|{%.+}}|%}", re.DOTALL)


# FIXME: This does not work for some reason
def is_simple_jinja(template_string: str) -> bool:
    return simple_jinja_regex.search(template_string) is None


# Funcs
@beartype
async def render_template_string(
    template_string: str,
    variables: dict,
    check: bool = False,
) -> str:
    # Parse template
    # TODO: Check that the string is indeed a jinjd template
    template = jinja_env.from_string(template_string)

    # If check is required, get required vars from template and validate variables
    if check:
        schema = to_json_schema(infer(template_string))
        validate(instance=variables, schema=schema)

    # Render
    rendered = await template.render_async(**variables)
    return rendered


# A render function that can render arbitrarily nested lists of dicts
# only render keys: content, text, image_url
# and only render values that are strings
T = TypeVar("T", str, dict, list[dict | list[dict]], None)


@beartype
async def render_template_nested(
    input: T,
    variables: dict,
    check: bool = False,
) -> T:
    match input:
        case str():
            return await render_template_string(input, variables, check)
        case dict():
            return {
                k: await render_template_nested(v, variables, check)
                for k, v in input.items()
            }
        case list():
            return [await render_template_nested(v, variables, check) for v in input]
        case _:
            return input


@beartype
async def render_template(
    input: str | list[dict],
    variables: dict,
    check: bool = False,
    skip_vars: list[str] | None = None,
) -> str | list[dict]:
    variables = {
        name: val
        for name, val in variables.items()
        if not (skip_vars is not None and isinstance(name, str) and name in skip_vars)
    }

    return await render_template_nested(input, variables, check)
