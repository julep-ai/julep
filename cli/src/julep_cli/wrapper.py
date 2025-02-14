import inspect
import typing
from collections.abc import Callable
from enum import Enum, StrEnum
from typing import Annotated, Any, Protocol

import questionary
import typer
from click.exceptions import MissingParameter, UsageError
from stringcase import titlecase
from typer import Typer


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
    parameter: typer.Argument, meta: tuple[typing.Any, ...], expected_type: type
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
    if not issubclass(expected_type, str | StrEnum | bool):
        prompt_message += f" [{expected_type.__name__}]"

    # Section: Extract additional keyword arguments from metadata
    kwargs = meta[2] if meta and len(meta) == 3 and isinstance(meta[2], dict) else {}
    kwargs["default"] = kwargs.get("default") or parameter.default
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
        kwargs["choices"] = choices = [e.value for e in expected_type]
        kwargs["default"] = kwargs["default"] or choices[0]

        if len(choices) >= 6:
            question_type = questionary.autocomplete
            prompt_message += f" [{len(choices)} options]"
            kwargs["complete_style"] = "MULTI_COLUMN"

        del kwargs["instruction"]

    # Section: Use confirmation prompt for booleans
    elif expected_type is bool:
        question_type = questionary.confirm
        kwargs["default"] = kwargs["default"] or False
        prompt_message += " (Y/n)" if kwargs["default"] else " (y/N)"

    else:
        # Section: Set default validation if not provided
        kwargs["validate"] = kwargs.get("validate") or make_validator(expected_type)

    # Section: Finalize instruction formatting
    if kwargs.get("instruction"):
        kwargs["instruction"] += " "

    if kwargs["default"] is None:
        del kwargs["default"]

    return question_type(prompt_message, **kwargs)


def prompt_for_missing_parameter(error: UsageError) -> None:
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

    # Section: Extract missing parameter details
    missing_param = error.param
    parameter_details = signature.parameters[missing_param.name]

    param_annotation = parameter_details.annotation
    type_args = typing.get_args(param_annotation)

    # Section: Determine expected type from annotation
    if len(type_args) >= 2 and isinstance(type_args[0], type):
        [expected_type, *_] = type_args
    else:
        expected_type = param_annotation or str

    # Section: Build and display prompt for missing parameter
    prompt = build_prompt(missing_param, type_args, expected_type)

    user_input = prompt.ask(patch_stdout=True)

    # Section: Bind user input to parameters
    bound = bind_arguments(signature, ctx.params | {missing_param.name: user_input})
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
    try:
        return command.main(map(str, cmd_args), standalone_mode=False)
    except BaseException as new_error:
        return prompt_for_missing_parameter(new_error)


class WrappedTyper(Typer):
    """Custom Typer subclass that handles missing parameters via interactive prompts."""

    def __call__(self, *args, **kwargs):
        """Invokes the Typer app and handles missing parameters gracefully."""
        # Section: Attempt to run the Typer app and catch errors
        try:
            return super().__call__(*args, **{**kwargs, "standalone_mode": False})
        except BaseException as error:
            return prompt_for_missing_parameter(error)

    def command(self, *args, **kwargs):
        """Decorator for registering commands with the Typer application."""
        return super().command(*args, **kwargs)


if __name__ == "__main__":
    # Example usage of WrappedTyper with an example command.
    from enum import StrEnum

    # Define an example enumeration for neural network types
    class NeuralNetwork(StrEnum):
        simple = "simple"
        conv = "conv"
        lstm = "lstm"
        b_simple = "b_simple"
        b_conv = "b_conv"
        b_lstm = "b_lstm"
        c_simple = "c_simple"
        c_conv = "c_conv"
        c_lstm = "c_lstm"

    app = WrappedTyper()

    @app.command()
    def hello(
        name: str,
        age: int,
        address: Annotated[
            str,
            typer.Argument(help="The address to use"),
            {"multiline": True},
        ],
        network: Annotated[
            NeuralNetwork,
            typer.Argument(help="The neural network to use"),
        ],
        wait: Annotated[
            bool,
            typer.Option(help="Wait for the task to complete"),
            {"default": True},
        ],
    ):
        """Example command that prints provided input arguments."""
        # Section: Print provided input arguments
        print(name)
        print(age)
        print(address)
        print(network)
        print(wait)

    app()
