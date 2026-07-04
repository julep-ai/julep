"""mem-mcp eval compat: the ``eval.py`` / ``eval.yaml`` *data* surface.

A mem-mcp ``.ctx`` package may carry consumer-side eval files: an ``eval.py``
exposing the ``sample(limit)`` / ``score(input, output, expected)`` contract
and an ``eval.yaml`` describing models/datasets/thresholds. This module ports
that data surface — the types from mem-mcp's ``dotctx.eval_types``, the
response-parsing helpers from ``dotctx.llm_utils``, and the loaders — so real
eval files load unchanged. It is data only: no runner, no scoring loops, no
mock-tool execution (Phase 3/4).

Loading a ``.ctx`` prompt NEVER executes eval code; :func:`load_ctx_evals` is
the one explicit entry point (``load_rich_dotctx`` does not call it).

Real ``eval.py`` files import ``from dotctx.eval_types import Sample`` /
``from dotctx import extract_llm_content``. :func:`load_eval_module` installs
``sys.modules`` aliases for ``dotctx`` / ``dotctx.eval_types`` /
``dotctx.llm_utils`` pointing at this module's namespace — ONLY for names not
already present in ``sys.modules`` (already-loaded real modules are never
clobbered) — and restores ``sys.modules`` in a ``finally``. CLI/test-time only;
the swap is process-global and not thread-safe (same caveat as the yglu env swap in
:mod:`julep.dotctx_yglu`).

Imports cleanly without the ``[dotctx]`` (jinja2) or ``[yglu]`` extras; yaml
and yglu load lazily inside the config loader.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import os
import sys
import types
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Mapping, Optional, TypeAlias, cast

# --------------------------------------------------------------------------- #
# eval_types port (1:1 from mem-mcp dotctx/eval_types.py).
# --------------------------------------------------------------------------- #
# Input = template variables (matches schema.pyi Input)
Input: TypeAlias = dict[str, Any]

# Output = whatever run_llm returns (opaque)
Output: TypeAlias = Any

# Score = 0.0 to 1.0
Score: TypeAlias = float


@dataclass
class Turn:
    """A single agent loop turn with tool call metadata."""

    output: Output
    tool_calls: list[dict[str, Any]]
    tool_results: list[Any]
    content: Optional[str]
    refusal: Optional[str]


# Stop function type: receives last turn and 1-based turn index
StopFn: TypeAlias = Callable[[Turn, int], bool]


def _default_stop_on() -> StopFn:
    return stop_after_turns(1)


def stop_after_turns(max_turns: int) -> StopFn:
    """Stop after a maximum number of turns (inclusive)."""

    def _stop(_last: Turn, turn_index: int) -> bool:
        return turn_index >= max_turns

    # Marker the ca eval runner reads to honor "stop_after_turns(n) -> max_rounds
    # override" without introspecting the opaque StopFn closure.
    _stop._ca_max_turns = max_turns  # type: ignore[attr-defined]
    return _stop


def stop_when_terminal_tool(tool_name: str, **kwargs: Any) -> StopFn:
    """Stop when a specific tool is called with matching args."""

    def _stop(last: Turn, _turn_index: int) -> bool:
        for call in last.tool_calls:
            if call.get("name") != tool_name:
                continue
            if not kwargs:
                return True
            args = call.get("args", {})
            if all(args.get(key) == value for key, value in kwargs.items()):
                return True
        return False

    return _stop


def stop_when_non_tool(*, allow_text_with_tools: bool = True) -> StopFn:
    """Stop when a turn has no tool calls (optionally treat text+tools as done)."""

    def _stop(last: Turn, _turn_index: int) -> bool:
        if not last.tool_calls:
            return True
        if not allow_text_with_tools and last.content:
            return True
        return False

    return _stop


def any_stop(*stops: StopFn) -> StopFn:
    """Combine stop functions with OR semantics."""

    def _stop(last: Turn, turn_index: int) -> bool:
        return any(stop(last, turn_index) for stop in stops)

    return _stop


def all_stop(*stops: StopFn) -> StopFn:
    """Combine stop functions with AND semantics."""

    def _stop(last: Turn, turn_index: int) -> bool:
        return all(stop(last, turn_index) for stop in stops)

    return _stop


@dataclass
class ExpectedToolCall:
    """Simplified tool call for eval comparison.

    Attributes:
        name: The function/tool name to match.
        arguments: Expected arguments. None means don't check args.
    """

    name: str
    arguments: dict[str, Any] | str | None = None


@dataclass
class Expected:
    """Expected output shape (mirrors ChatCompletionAssistantMessage).

    All fields are optional. If all are None, this represents a smoke test
    that just verifies the prompt runs without error.

    Attributes:
        content: Expected text content in the response.
        tool_calls: Expected tool/function calls.
        refusal: Expected refusal message.
    """

    content: Optional[str] = None
    tool_calls: Optional[list[ExpectedToolCall]] = None
    refusal: Optional[str] = None


@dataclass
class Sample:
    """A single eval test case.

    Attributes:
        input: Template variables to render the prompt.
        expected: Expected output for comparison. None = smoke test.
        mock_tools: Mock tool responses for agent evaluation.
        stop_on: Stop function for agent loops (defaults to stop_after_turns(1)).
        expected_calls: Optional call groups for agent loop scoring.
        tags: Tags for filtering samples.
        name: Optional name for identification in reports.
    """

    input: Input
    expected: Optional[Expected] = None
    mock_tools: dict[str, Any] = field(default_factory=dict)
    stop_on: StopFn = field(default_factory=_default_stop_on)
    expected_calls: Optional[list[list[dict[str, Any]]]] = None
    tags: list[str] = field(default_factory=list)
    name: Optional[str] = None


@dataclass
class MockToolConfig:
    """Configuration for mocking a tool with argument-based matching.

    Attributes:
        match: List of (arg_pattern, response) tuples. First matching pattern wins.
            arg_pattern is a dict - all specified keys must match (partial match).
        default: Default response if no match patterns match.
        responses: Sequential responses (cycles if exhausted). Used if no match defined.
    """

    match: list[tuple[dict[str, Any], Any]] = field(default_factory=list)
    default: Any = None
    responses: list[Any] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# llm_utils port (1:1 from mem-mcp dotctx/llm_utils.py).
# --------------------------------------------------------------------------- #
def strip_markdown_codeblock(text: str) -> str:
    """Strip markdown code block fences from LLM output.

    Handles ```json\\n...\\n``` and bare ``` fences, plus malformed blocks
    with missing newlines.
    """
    text = text.strip()

    if not text.startswith("```"):
        return text

    lines = text.split("\n")

    if len(lines) > 2:
        # Normal case: ```json\n...\n``` — drop first and last lines.
        return "\n".join(lines[1:-1]).strip()

    # Malformed: everything on one/two lines
    text = text.lstrip("`").rstrip("`")
    if text.startswith("json"):
        text = text[4:]

    return text.strip()


def extract_llm_content(response: Any) -> Optional[str]:
    """Extract text content from various LLM response formats.

    Handles OpenAI-compatible response objects
    (``response.choices[0].message.content``), dict responses (direct
    ``content`` key or nested ``choices``), and objects with a nested
    ``.output`` attribute (recursively). Returns None when not found.
    """
    # OpenAI-compatible response object: response.choices[0].message.content
    if hasattr(response, "choices") and response.choices:
        msg = response.choices[0].message
        return cast(Optional[str], getattr(msg, "content", None))

    # Dict format
    if isinstance(response, dict):
        # Direct content key
        if "content" in response:
            return cast(Optional[str], response.get("content"))

        # Nested choices format
        choices = response.get("choices", [])
        if choices:
            msg = choices[0].get("message", {})
            return cast(Optional[str], msg.get("content"))

    # Nested .output attribute (e.g., some eval wrappers)
    output_attr = getattr(response, "__dict__", {}).get("output")
    if output_attr is not None:
        return extract_llm_content(output_attr)

    return None


def parse_llm_json(content: str) -> Any:
    """Parse JSON from LLM output, stripping markdown fences first.

    Raises :class:`json.JSONDecodeError` if the content is not valid JSON
    after stripping.
    """
    cleaned = strip_markdown_codeblock(content)
    return json.loads(cleaned)


# --------------------------------------------------------------------------- #
# eval.py loading behind the sys.modules compat shim.
# --------------------------------------------------------------------------- #
_EVAL_TYPES_EXPORTS = (
    "Input", "Output", "Score", "Turn", "StopFn",
    "stop_after_turns", "stop_when_terminal_tool", "stop_when_non_tool",
    "any_stop", "all_stop",
    "ExpectedToolCall", "Expected", "Sample", "MockToolConfig",
)
_LLM_UTILS_EXPORTS = ("strip_markdown_codeblock", "extract_llm_content", "parse_llm_json")

_EVAL_MODULE_COUNTER = itertools.count()


def _install_dotctx_shims() -> list[str]:
    """Alias ``dotctx`` / submodules to this module for unloaded names.

    Returns the installed keys; the caller must hand them back to
    :func:`_remove_dotctx_shims` in a ``finally``. Modules that are already in
    ``sys.modules`` are never clobbered, but an installed-yet-unloaded
    third-party ``dotctx`` package does not change this loader's return types.
    """
    here = sys.modules[__name__]
    exports = {
        # mem-mcp's dotctx/__init__.py re-exports both submodules' names.
        "dotctx": _EVAL_TYPES_EXPORTS + _LLM_UTILS_EXPORTS,
        "dotctx.eval_types": _EVAL_TYPES_EXPORTS,
        "dotctx.llm_utils": _LLM_UTILS_EXPORTS,
    }
    shims: dict[str, types.ModuleType] = {}
    for name, attrs in exports.items():
        if name in sys.modules:
            continue
        shim = types.ModuleType(name)
        shim.__doc__ = "julep compat alias for mem-mcp dotctx (eval loading only)"
        for attr in attrs:
            setattr(shim, attr, getattr(here, attr))
        shims[name] = shim

    parent = shims.get("dotctx")
    installed: list[str] = []
    for name, shim in shims.items():
        if parent is not None and "." in name:  # dotctx.eval_types attribute access
            setattr(parent, name.split(".", 1)[1], shim)
        sys.modules[name] = shim
        installed.append(name)
    return installed


def _remove_dotctx_shims(installed: list[str]) -> None:
    for name in installed:
        sys.modules.pop(name, None)


@dataclass(frozen=True)
class EvalModule:
    """Loaded eval.py module with sample and score functions.

    Attributes:
        sample: Function that generates test samples.
        score: Function that scores outputs against expected values.
        source_path: Path to the eval.py file.
    """

    sample: Callable[[int], list[Sample] | Awaitable[list[Sample]]]
    score: Callable[[Input, Output, Optional[Expected]], Score | Awaitable[Score]]
    source_path: str


def load_eval_module(path: str) -> EvalModule:
    """Dynamically import an ``eval.py`` and extract sample/score functions.

    Executes arbitrary code — never called during prompt loading; only from
    the explicit :func:`load_ctx_evals` entry point (or directly). The dotctx
    compat shim is installed around the exec and restored in a ``finally``
    (see module docstring for the thread-safety caveat).
    """
    if not os.path.exists(path):
        raise ValueError(f"eval.py not found at {path}")
    if not os.path.isfile(path):
        raise ValueError(f"eval.py path is not a file: {path}")

    # Unique module name so repeated loads never collide (mirrors mem-mcp).
    parent = os.path.basename(os.path.dirname(os.path.abspath(path)))
    module_name = f"dotctx_eval_{parent}_{next(_EVAL_MODULE_COUNTER)}"

    installed = _install_dotctx_shims()
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Failed to create module spec for {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module  # allow self-imports during exec
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            raise ValueError(f"Failed to execute eval.py: {e}") from e
    finally:
        sys.modules.pop(module_name, None)
        _remove_dotctx_shims(installed)

    sample_fn = getattr(module, "sample", None)
    score_fn = getattr(module, "score", None)

    if sample_fn is None:
        raise ValueError(
            "eval.py missing required 'sample' function. "
            "Expected: def sample(limit: int) -> list[Sample]"
        )
    if score_fn is None:
        raise ValueError(
            "eval.py missing required 'score' function. "
            "Expected: def score(input: Input, output: Output, expected: Expected | None) -> Score"
        )
    if not callable(sample_fn):
        raise ValueError("'sample' in eval.py is not callable")
    if not callable(score_fn):
        raise ValueError("'score' in eval.py is not callable")

    return EvalModule(sample=sample_fn, score=score_fn, source_path=path)


# --------------------------------------------------------------------------- #
# eval.yaml as data.
# --------------------------------------------------------------------------- #
_ALLOWED_EVAL_CONFIG_KEYS = frozenset(
    {"models", "datasets", "threshold", "concurrency", "scoring", "agent", "profiles"}
)


@dataclass(frozen=True)
class ModelSpec:
    """Model definition for eval configuration."""

    id: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class DatasetSpec:
    """Dataset file definition, resolved against the eval.yaml directory."""

    file: str
    format: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvalConfig:
    """Loaded eval.yaml contents — data only, no evaluation execution.

    ``profiles`` stays raw (name -> override mapping in the same shape as the
    top level); resolving a profile into an executable config is a runner
    concern (Phase 3/4). Defaults mirror mem-mcp's resolver: threshold 0.5,
    concurrency 5.
    """

    source_path: str
    models: tuple[ModelSpec, ...]
    datasets: tuple[DatasetSpec, ...]
    threshold: float
    concurrency: int
    scoring: dict[str, Any]
    agent: dict[str, Any]
    profiles: dict[str, dict[str, Any]]


def _str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item) for item in value if item)
    return (str(value),)


def _parse_models(raw: Any, origin: str) -> tuple[ModelSpec, ...]:
    models: list[ModelSpec] = []
    for item in raw or []:
        if isinstance(item, str):
            models.append(ModelSpec(id=item))
            continue
        if not isinstance(item, dict) or "id" not in item:
            raise ValueError(
                f"each model in {origin!r} must be a string or a mapping with an id"
            )
        models.append(ModelSpec(id=str(item["id"]), tags=_str_tuple(item.get("tags"))))
    return tuple(models)


def _parse_datasets(raw: Any, base_dir: str, origin: str) -> tuple[DatasetSpec, ...]:
    datasets: list[DatasetSpec] = []
    for item in raw or []:
        if isinstance(item, str):
            item = {"file": item}
        if not isinstance(item, dict) or "file" not in item:
            raise ValueError(f"each dataset in {origin!r} must specify a file")
        file_path = os.path.join(base_dir, str(item["file"]))
        format_name = str(item.get("format") or os.path.splitext(file_path)[1].lstrip("."))
        datasets.append(
            DatasetSpec(file=file_path, format=format_name, tags=_str_tuple(item.get("tags")))
        )
    return tuple(datasets)


def _coerce_number(value: Any, *, key: str, origin: str, want_int: bool) -> float:
    # Yglu/env values arrive as strings; numeric strings coerce (same rule as
    # the settings loaders), anything else is a loud teaching error.
    try:
        return int(str(value)) if want_int else float(str(value))
    except (TypeError, ValueError):
        raise ValueError(
            f"eval.yaml {key} in {origin!r} must be a number, got {value!r}"
        ) from None


def _mapping_key(raw: Mapping[str, Any], key: str, origin: str) -> dict[str, Any]:
    value = raw[key] if key in raw else {}
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError(f"eval.yaml {key} in {origin!r} must be a mapping")
    return dict(value)


def load_eval_config(path: str, *, env: Optional[Mapping[str, str]] = None) -> EvalConfig:
    """Load an ``eval.yaml``/``eval.yml`` into an :class:`EvalConfig`.

    Yglu-aware with the same explicit ``env=`` binding as the settings
    loaders: ``$env`` never reads the ambient process environment.
    """
    if not os.path.exists(path):
        raise ValueError(f"eval config not found at {path}")
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    from .dotctx_yglu import has_yglu_tags, load_settings as load_yglu_settings

    if has_yglu_tags(text):
        raw = load_yglu_settings(text, env=env, filepath=path)
    else:
        import yaml

        raw = yaml.safe_load(text) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"eval.yaml must be a YAML mapping: {path!r}")

    unknown = sorted(set(raw) - _ALLOWED_EVAL_CONFIG_KEYS)
    if unknown:
        raise ValueError(
            f"unknown eval.yaml keys in {path!r}: {', '.join(unknown)} "
            f"(allowed: {', '.join(sorted(_ALLOWED_EVAL_CONFIG_KEYS))})"
        )

    profiles = _mapping_key(raw, "profiles", path)
    for name, override in profiles.items():
        if not isinstance(override, dict):
            raise ValueError(f"eval.yaml profile {name!r} in {path!r} must be a mapping")

    base_dir = os.path.dirname(os.path.abspath(path))
    threshold = raw.get("threshold")
    concurrency = raw.get("concurrency")
    return EvalConfig(
        source_path=path,
        models=_parse_models(raw.get("models"), path),
        datasets=_parse_datasets(raw.get("datasets"), base_dir, path),
        threshold=(
            0.5 if threshold is None
            else _coerce_number(threshold, key="threshold", origin=path, want_int=False)
        ),
        concurrency=(
            5 if concurrency is None
            else int(_coerce_number(concurrency, key="concurrency", origin=path, want_int=True))
        ),
        scoring=_mapping_key(raw, "scoring", path),
        agent=_mapping_key(raw, "agent", path),
        profiles=profiles,
    )


# --------------------------------------------------------------------------- #
# The one explicit entry point.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CtxEvals:
    """A package's eval files, loaded on demand — either may be absent."""

    eval_module: Optional[EvalModule]
    eval_config: Optional[EvalConfig]


def load_ctx_evals(ctx_dir: str, *, env: Optional[Mapping[str, str]] = None) -> CtxEvals:
    """Load a ``.ctx`` directory's eval.py + eval.yaml (each Optional).

    The ONE explicit entry point for eval loading — prompt loading
    (``load_dotctx`` / ``load_rich_dotctx``) never calls it, so importing a
    prompt package never executes eval code.
    """
    if not os.path.isdir(ctx_dir):
        raise ValueError(
            f"load_ctx_evals expects a .ctx directory: {ctx_dir!r} "
            "(single-file .ctx packages carry no eval files)"
        )

    eval_module: Optional[EvalModule] = None
    eval_py = os.path.join(ctx_dir, "eval.py")
    if os.path.exists(eval_py):
        eval_module = load_eval_module(eval_py)

    eval_config: Optional[EvalConfig] = None
    for fn in ("eval.yaml", "eval.yml"):
        cand = os.path.join(ctx_dir, fn)
        if os.path.exists(cand):
            eval_config = load_eval_config(cand, env=env)
            break

    return CtxEvals(eval_module=eval_module, eval_config=eval_config)


__all__ = [
    "CtxEvals",
    "DatasetSpec",
    "EvalConfig",
    "EvalModule",
    "Expected",
    "ExpectedToolCall",
    "Input",
    "MockToolConfig",
    "ModelSpec",
    "Output",
    "Sample",
    "Score",
    "StopFn",
    "Turn",
    "all_stop",
    "any_stop",
    "extract_llm_content",
    "load_ctx_evals",
    "load_eval_config",
    "load_eval_module",
    "parse_llm_json",
    "stop_after_turns",
    "stop_when_non_tool",
    "stop_when_terminal_tool",
    "strip_markdown_codeblock",
]
