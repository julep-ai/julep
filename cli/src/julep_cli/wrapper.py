import inspect
import os
import sys
import typing
from collections.abc import Callable
from enum import Enum, IntEnum, StrEnum
from functools import wraps
from pathlib import Path
from typing import Any, Protocol

import questionary
import typer
from click.exceptions import Abort, MissingParameter, UsageError
from questionary import Choice
from stringcase import titlecase
from typer import Typer

from .style import custom_style


def except_abort(target_func: Callable) -> Callable:
    def catch_abort(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseException as error:
                if isinstance(error, Abort | KeyboardInterrupt):
                    print("\nExiting")
                    sys.exit(1)

                return target_func(error)

        return wrapper

    return catch_abort


class DocIntEnum(IntEnum):
    def __new__(cls, value, doc=None):
        self = int.__new__(cls, value)  # calling super().__new__(value) here would fail
        self._value_ = value
        if doc is not None:
            self.__doc__ = doc
        return self


class DocStrEnum(StrEnum):
    def __new__(cls, value, doc=None):
        self = str.__new__(cls, value)  # calling super().__new__(value) here would fail
        self._value_ = value
        if doc is not None:
            self.__doc__ = doc
        return self


def to_relative(path: Path | str) -> str:
    if isinstance(path, str):
        return os.path.relpath(path)

    if isinstance(path, Path):
        return str(path.relative_to(Path(".").resolve()))

    raise NotImplementedError


class ExceptionWithContext(Protocol):
    __context__: UsageError


def get_command_signature(error: UsageError) -> inspect.Signature:
    """Extracts the function signature from the callback of a UsageError's command."""
    return inspect.signature(error.cmd.callback)


def bind_arguments(signature: inspect.Signature, params: dict) -> inspect.BoundArguments:
    """Binds provided parameters to the given signature and applies default values."""
    bound = signature.bind_partial(**params)
    bound.apply_defaults()

    return bound


def make_validator(func: Callable[[Any], Any]) -> Callable[[Any], bool]:
    def validate(value: Any) -> bool:
        try:
            func(value)
            return True
        except Exception:
            return False

    return validate


def build_prompt(
    parameter: typer.Argument,
    meta: tuple[typing.Any, ...],
    expected_type: type,
    enable_search: bool = True,
) -> questionary.Question:
    """Prepares a questionary prompt based on the parameter metadata and expected type.

    Args:
        parameter: Typer argument parameter.
        meta: Tuple of type specifications and additional metadata.
        expected_type: Expected type for the parameter.

    Returns:
        A questionary.Question object for prompting the user.
    """
    # Section: Build prompt header
    prompt_message = titlecase(parameter.human_readable_name.lower())

    # Section: Append type indicator to prompt message
    if not issubclass(expected_type, str | Enum | bool):
        prompt_message += f" [{expected_type.__name__}]"

    # Section: Extract additional keyword arguments from metadata
    kwargs = meta[2] if meta and len(meta) == 3 and isinstance(meta[2], dict) else {}
    kwargs["default"] = kwargs.get("default") or parameter.default
    kwargs["style"] = kwargs.get("style") or custom_style
    question_type = questionary.text

    # Section: Add instruction based on parameter help
    kwargs["instruction"] = kwargs.get("instruction") or (
        f"({parameter.help})" if parameter.help else ""
    )

    # Section: Handle multiline input
    if kwargs.get("multiline", False):
        kwargs["instruction"] += "\n(Press Alt+Enter or Esc then Enter to submit)\n"

    # Section: Configure prompt for Enum types
    if issubclass(expected_type, Enum):
        question_type = questionary.select
        kwargs["choices"] = choices = [
            Choice(value=e.name, title=getattr(e, "__doc__", None) or e.value)
            for e in expected_type
        ]

        kwargs["default"] = kwargs["default"] or choices[0].value
        use_autocomplete = kwargs.pop("use_autocomplete", False)

        if enable_search and not use_autocomplete:
            kwargs["use_jk_keys"] = False
            kwargs["use_search_filter"] = True

        if use_autocomplete:
            question_type = questionary.autocomplete
            prompt_message += f" [{len(choices)} options]"
            kwargs["complete_style"] = "MULTI_COLUMN"

        del kwargs["instruction"]

    # Section: Use confirmation prompt for booleans
    elif expected_type is bool:
        question_type = questionary.confirm
        kwargs["default"] = kwargs["default"] or False
        prompt_message += " (Y/n)" if kwargs["default"] else " (y/N)"

    # Section: Use confirmation prompt for booleans
    elif expected_type is Path:
        question_type = questionary.path
        kwargs["default"] = path = kwargs["default"] or "."

        # Need to convert to string and find shorter variant (relative or absolute)
        relative = to_relative(path)
        kwargs["default"] = relative if len(relative) < len(str(path)) else str(path)

        del kwargs["instruction"]

    else:
        # Section: Set default validation if not provided
        kwargs["validate"] = kwargs.get("validate") or make_validator(expected_type)

    # Section: Finalize instruction formatting
    if kwargs.get("instruction"):
        kwargs["instruction"] += " "

    if kwargs["default"] is None:
        del kwargs["default"]

    # if default is a function, call it
    if callable(kwargs["default"]):
        kwargs["default"] = kwargs["default"]()

    return question_type(prompt_message, **kwargs)


def build_form(signature: inspect.Signature, ctx: typer.Context) -> questionary.Form:
    form_fields = {}

    # Section: Bind user input to parameters
    bound = bind_arguments(signature, ctx.params)

    # Section: Construct form from bound parameters
    for param_item in ctx.command.params:
        if param_item.name in bound.arguments:
            continue

        parameter_details = signature.parameters[param_item.name]
        param_annotation = parameter_details.annotation
        type_args = typing.get_args(param_annotation)

        # Section: Determine expected type from annotation
        if len(type_args) >= 2 and isinstance(type_args[0], type):
            [expected_type, *_] = type_args
        else:
            expected_type = param_annotation or str

        # Section: Build and display prompt for missing parameter
        prompt = build_prompt(param_item, type_args, expected_type)
        form_fields[param_item.name] = prompt

    return questionary.form(**form_fields)


def prompt_for_missing_parameters(error: UsageError) -> None:
    """Prompts for missing parameters and re-invokes the command after receiving input."""
    # Section: Unwrap nested error if applicable
    if not isinstance(error, MissingParameter) and hasattr(error, "__context__"):
        error = getattr(error, "__context__")

    # Section: Reraise if error is not a MissingParameter
    if not isinstance(error, MissingParameter):
        raise error

    # Section: Retrieve command signature and context
    signature = get_command_signature(error)
    ctx = error.ctx
    command = error.cmd

    # Section: Build and display prompt for missing parameter
    form = build_form(signature, ctx)
    user_input = form.ask(patch_stdout=True)
    if not user_input:
        print("Exiting")  # No newline needed, since questionary already prints one
        sys.exit(1)

    # Section: Bind user input to parameters
    bound = bind_arguments(signature, ctx.params | user_input)
    cmd_args = []

    # Section: Construct command arguments from bound parameters
    for param_item in ctx.command.params:
        if param_item.name not in bound.arguments:
            continue

        # Retrieve option flag
        [option_flag, *_] = param_item.to_info_dict()["opts"]
        is_option = isinstance(param_item, typer.core.TyperOption)
        value = bound.arguments[param_item.name]
        param_type = bound.signature.parameters[param_item.name].annotation
        param_type = getattr(param_type, "__origin__", param_type)

        # Section: Process option parameters
        if is_option:
            if param_type is bool:
                prefix = "no-" if not value else ""
                cmd_args.append(f"--{prefix}{option_flag[2:]}")
            else:
                cmd_args.append(option_flag)
                cmd_args.append(value)
        else:
            cmd_args.append(value)

    # Section: Reinvoke the command with updated arguments
    return command.main(map(str, cmd_args), standalone_mode=False)


class WrappedTyper(Typer):
    """Custom Typer subclass that handles missing parameters via interactive prompts."""

    @except_abort(prompt_for_missing_parameters)
    def __call__(self, *args, **kwargs):
        """Invokes the Typer app and handles missing parameters gracefully."""
        # Section: Attempt to run the Typer app and catch errors
        return super().__call__(*args, **{**kwargs, "standalone_mode": False})
