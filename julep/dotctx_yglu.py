"""Native ``settings.yaml`` evaluator with an explicit ``$env`` binding.

mem-mcp's ``.ctx`` settings use tagged expressions — universally
``!? $env.get("VAR", default)`` — for env-dependent model/round config. To keep
freezes deterministic, ``$env`` never reads the ambient process environment:
callers pass the mapping (the Julep env profile). The built-in evaluator uses
only that binding and is thread-safe.

Deployed workers: with no binding, tagged settings evaluate to their
*defaults*. A Temporal worker that imports ``.ctx`` packages must call
:func:`set_default_env` with the same env profile the artifact was frozen
against (``julep.toml`` ``[env.<name>.vars]``) *before* those imports, or its
registry can disagree with the frozen identity. Persisting the resolved
reasoner config into the artifact (so workers need no manual binding) is
deferred to the deployment phase.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Optional

import yaml

_TAG_RE = re.compile(r"!\?|!\(\)|!if\b|!for\b|!concat\b|!merge\b")
_YGLU_TAG_SUFFIXES = frozenset({"?", "()", "if", "for", "concat", "merge"})
_DEFAULT_ENV: Optional[Mapping[str, str]] = None
_NUMBER_RE = re.compile(r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")


def has_yglu_tags(text: str) -> bool:
    """Return whether ``text`` carries a yglu tag at an actual YAML tag position.

    Detection is structural (scanner tokens), so punctuation inside scalars —
    ``system: "Really!?"`` — is content, not a tag. Text the scanner rejects
    falls back to the regex: an unscannable file fails to load either way, and
    the tagged route reports the more useful error.
    """
    try:
        return any(
            isinstance(token, yaml.TagToken)
            and token.value[0] == "!"
            and token.value[1] in _YGLU_TAG_SUFFIXES
            for token in yaml.scan(text)
        )
    except yaml.YAMLError:
        return _TAG_RE.search(text) is not None


def set_default_env(env: Optional[Mapping[str, str]]) -> None:
    """Set the env binding used when callers pass ``env=None``."""
    global _DEFAULT_ENV
    _DEFAULT_ENV = None if env is None else dict(env)


def default_env() -> Optional[Mapping[str, str]]:
    """Return the env binding used when callers pass ``env=None``."""
    return _DEFAULT_ENV


def _configuration_error(filepath: str, offending: str) -> ValueError:
    return ValueError(
        f"Unsupported yglu configuration in {filepath!r}: {offending}. "
        "The yglu dependency was removed in 3.0.0rc5; only `$env.get(...)` "
        "expressions are supported in `!?` tags. Move env-dependent config to "
        "run input/metadata."
    )


class _ExpressionParser:
    """Parse the intentionally small expression language used by ``!?`` tags."""

    # AIDEV-NOTE: Supported grammar is expr := env_get | string_literal |
    # number_literal, where env_get recursively accepts an optional expr default.
    def __init__(self, expression: str, env: Mapping[str, str]) -> None:
        self._expression = expression
        self._env = env
        self._position = 0

    def parse(self) -> Any:
        """Parse and evaluate the complete expression."""
        value = self._parse_expr()
        self._skip_whitespace()
        if self._position != len(self._expression):
            raise ValueError("trailing content")
        return value

    def _parse_expr(self) -> Any:
        self._skip_whitespace()
        if self._expression.startswith("$env", self._position):
            return self._parse_env_get()
        if self._peek() in {"'", '"'}:
            return self._parse_string()
        return self._parse_number()

    def _parse_env_get(self) -> Any:
        self._expect("$env")
        self._skip_whitespace()
        self._expect(".")
        self._skip_whitespace()
        self._expect("get")
        self._skip_whitespace()
        self._expect("(")
        self._skip_whitespace()
        name = self._parse_string()
        self._skip_whitespace()
        if self._consume(")"):
            return self._env.get(name)
        self._expect(",")
        default = self._parse_expr()
        self._skip_whitespace()
        self._expect(")")
        return self._env.get(name, default)

    def _parse_string(self) -> str:
        quote = self._peek()
        if quote not in {"'", '"'}:
            raise ValueError("expected a quoted string")
        self._position += 1
        value: list[str] = []
        escapes = {
            '"': '"',
            "'": "'",
            "\\": "\\",
            "n": "\n",
            "t": "\t",
            "r": "\r",
            "b": "\b",
            "f": "\f",
        }
        while self._position < len(self._expression):
            char = self._expression[self._position]
            self._position += 1
            if char == quote:
                return "".join(value)
            if char != "\\":
                value.append(char)
                continue
            if self._position == len(self._expression):
                raise ValueError("unterminated escape sequence")
            escaped = self._expression[self._position]
            self._position += 1
            if escaped not in escapes:
                raise ValueError(f"unsupported escape sequence \\{escaped}")
            value.append(escapes[escaped])
        raise ValueError("unterminated string")

    def _parse_number(self) -> int | float:
        match = _NUMBER_RE.match(self._expression, self._position)
        if match is None:
            raise ValueError("expected `$env.get(...)`, a string, or a number")
        literal = match.group(0)
        self._position = match.end()
        return float(literal) if any(char in literal for char in ".eE") else int(literal)

    def _skip_whitespace(self) -> None:
        while self._peek().isspace():
            self._position += 1

    def _peek(self) -> str:
        if self._position == len(self._expression):
            return ""
        return self._expression[self._position]

    def _consume(self, token: str) -> bool:
        if not self._expression.startswith(token, self._position):
            return False
        self._position += len(token)
        return True

    def _expect(self, token: str) -> None:
        if not self._consume(token):
            raise ValueError(f"expected {token!r}")


class _SettingsLoader(yaml.SafeLoader):
    """Safe YAML loader carrying the explicit expression evaluation context."""

    def __init__(self, stream: str, *, env: Mapping[str, str], filepath: str) -> None:
        super().__init__(stream)
        self.env = env
        self.filepath = filepath


def _construct_expression(loader: _SettingsLoader, node: yaml.Node) -> Any:
    if not isinstance(node, yaml.ScalarNode):
        node_kind = "mapping" if isinstance(node, yaml.MappingNode) else "sequence"
        raise _configuration_error(
            loader.filepath, f"tag {node.tag!r} on a non-scalar {node_kind} node"
        )
    expression = loader.construct_scalar(node)
    try:
        return _ExpressionParser(expression, loader.env).parse()
    except ValueError as exc:
        raise _configuration_error(loader.filepath, f"tag `!? {expression}`") from exc


def _construct_unsupported_tag(loader: _SettingsLoader, node: yaml.Node) -> Any:
    raise _configuration_error(loader.filepath, f"tag {node.tag!r}")


_SettingsLoader.add_constructor("!?", _construct_expression)
for _tag_suffix in _YGLU_TAG_SUFFIXES - {"?"}:
    _SettingsLoader.add_constructor(f"!{_tag_suffix}", _construct_unsupported_tag)


def load_settings(text: str, *, env: Optional[Mapping[str, str]], filepath: str) -> dict[str, Any]:
    """Load settings using only the supported native ``!?`` expression grammar."""
    binding = dict(env) if env is not None else dict(default_env() or {})
    loader = _SettingsLoader(text, env=binding, filepath=filepath)
    try:
        result: Any = loader.get_single_data()
    finally:
        loader.dispose()  # type: ignore[no-untyped-call]
    settings: Any = {} if result is None else result
    if not isinstance(settings, dict):
        raise ValueError(f"settings must be a YAML mapping: {filepath!r}")
    return settings


__all__ = ["default_env", "has_yglu_tags", "load_settings", "set_default_env"]
