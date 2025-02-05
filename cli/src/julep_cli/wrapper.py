import inspect
import typing
from enum import Enum
from typing import Annotated, Any, Protocol

import questionary
import typer
from click.exceptions import MissingParameter, UsageError
from stringcase import titlecase
from typer import Typer


class ExceptionWithContext(Protocol):
    __context__: UsageError


def get_signature_from_exc(exc: UsageError) -> inspect.Signature:
    return inspect.signature(exc.cmd.callback)


def get_bound_args(sig: inspect.Signature, params: dict) -> inspect.BoundArguments:
    bound = sig.bind_partial(**params)
    bound.apply_defaults()

    return bound


def prepare_question(
    param: typer.Argument, args: tuple[typing.Any, ...], arg_type: type
) -> questionary.Question:
    msg = titlecase(param.human_readable_name)

    if arg_type is bool:
        msg += " (y/N)"
    elif arg_type is not str:
        msg += f" [{arg_type.__name__}]"

    kwargs = args[2] if args and len(args) == 3 and isinstance(args[2], dict) else {}
    question_type = questionary.text

    if not kwargs.get("validate"):

        def validate(x: Any) -> bool:
            try:
                arg_type(x)
                return True
            except Exception:
                return False

        kwargs["validate"] = validate

    kwargs["instruction"] = f"({param.help})" if param.help else ""

    if kwargs.get("multiline", False):
        kwargs["instruction"] += "\n(Press Alt+Enter or Esc then Enter to submit)\n"
        del kwargs["validate"]

    if issubclass(arg_type, Enum):
        kwargs["choices"] = choices = [e.value for e in arg_type]
        question_type = questionary.select

        if len(choices) >= 6:
            question_type = questionary.autocomplete
            msg += f" [search {len(choices)} options]"

        del kwargs["instruction"]
        del kwargs["validate"]

    if arg_type is bool:
        question_type = questionary.confirm
        kwargs["default"] = False
        del kwargs["validate"]

    if kwargs.get("instruction"):
        kwargs["instruction"] += " "

    return question_type(
        msg,
        **kwargs,
    )


def handle_missing_param(exc: UsageError) -> None:
    if not isinstance(exc, MissingParameter) and hasattr(exc, "__context__"):
        exc = getattr(exc, "__context__")

    if not isinstance(exc, MissingParameter):
        raise exc

    sig = get_signature_from_exc(exc)
    click_ctx = exc.ctx
    cmd = exc.cmd

    param = exc.param
    sig_param = sig.parameters[param.name]

    annotation = sig_param.annotation
    args = typing.get_args(annotation)
    arg_type = args[0] if len(args) >= 2 and isinstance(args[0], type) else (annotation or str)
    question = prepare_question(param, args, arg_type)

    result = question.ask(patch_stdout=True)
    bound = get_bound_args(sig, click_ctx.params | {param.name: result})

    cmd_args = []

    for _param in click_ctx.command.params:
        if _param.name not in bound.arguments:
            continue

        opt_flag = _param.to_info_dict()["opts"][0]
        is_typer_option = isinstance(_param, typer.core.TyperOption)
        value = bound.arguments[_param.name]

        if is_typer_option:
            if arg_type is bool:
                prefix = "no-" if not value else ""
                cmd_args.append(f"--{prefix}{opt_flag[2:]}")
            else:
                cmd_args.append(opt_flag)
                cmd_args.append(value)

        else:
            cmd_args.append(value)

    try:
        return cmd.main(map(str, cmd_args), standalone_mode=False)
    except BaseException as new_exc:
        return handle_missing_param(new_exc)


class WrappedTyper(Typer):
    def __call__(self, *args, **kwargs):
        try:
            super().__call__(*args, **{**kwargs, "standalone_mode": False})
        except BaseException as exc:
            return handle_missing_param(exc)

    def command(self, *args, **kwargs):
        return super().command(
            *args,
            **kwargs,
        )


if __name__ == "__main__":
    from enum import StrEnum

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
        ],
    ):
        print(name)
        print(age)
        print(address)
        print(network)
        print(wait)

    app()
