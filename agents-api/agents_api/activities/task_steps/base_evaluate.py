import ast
from typing import Any

from beartype import beartype
from box import Box
from openai import BaseModel
from simpleeval import NameNotDefined
from temporalio import activity
from thefuzz import fuzz

from ...common.storage_handler import auto_blob_store
from ...env import testing
from ..utils import get_evaluator


class EvaluateError(Exception):
    def __init__(self, error, expression, values):
        error_message = error.message if hasattr(error, "message") else str(error)
        message = error_message

        # Catch a possible jinja template error
        if "unhashable" in error_message and "{{" in expression:
            message += "\nSuggestion: It seems like you used a jinja template, did you mean to use a python expression?"

        # Catch a possible misspell in a variable name
        if isinstance(error, NameNotDefined):
            misspelledName = error_message.split("'")[1]
            for variableName in values.keys():
                if fuzz.ratio(variableName, misspelledName) >= 90.0:
                    message += f"\nDid you mean '{variableName}' instead of '{misspelledName}'?"
        super().__init__(message)


@auto_blob_store
@beartype
async def base_evaluate(
    exprs: str | list[str] | dict[str, str] | dict[str, dict[str, str]],
    values: dict[str, Any] = {},
    extra_lambda_strs: dict[str, str] | None = None,
) -> Any | list[Any] | dict[str, Any]:
    input_len = 1 if isinstance(exprs, str) else len(exprs)
    assert input_len > 0, "exprs must be a non-empty string, list or dict"

    extra_lambdas = {}
    if extra_lambda_strs:
        for k, v in extra_lambda_strs.items():
            v = v.strip()

            # Check that all extra lambdas are valid
            assert v.startswith("lambda "), "All extra lambdas must start with 'lambda'"

            try:
                ast.parse(v)
            except Exception as e:
                raise ValueError(f"Invalid lambda: {v}") from e

            # Eval the lambda and add it to the extra lambdas
            extra_lambdas[k] = eval(v)

    # Turn the nested dict values from pydantic to dicts where possible
    values = {
        k: v.model_dump() if isinstance(v, BaseModel) else v for k, v in values.items()
    }

    # frozen_box doesn't work coz we need some mutability in the values
    values = Box(values, frozen_box=False, conversion_box=True)

    evaluator = get_evaluator(names=values, extra_functions=extra_lambdas)

    chosen_expression = ""

    try:
        result = None
        match exprs:
            case str():
                chosen_expression = exprs
                result = evaluator.eval(exprs)
            case list():
                result = []
                for expr in exprs:
                    chosen_expression = expr
                    result.append(evaluator.eval(expr))
            case dict() as d if all(
                isinstance(v, dict) or isinstance(v, str) for v in d.values()
            ):
                result = {}
                for k, v in d.items():
                    if isinstance(v, str):
                        chosen_expression = v
                        result[k] = evaluator.eval(v)
                    else:
                        result[k] = {}
                        for k1, v1 in v.items():
                            chosen_expression = v1
                            result[k][k1] = evaluator.eval(v1)
            case _:
                raise ValueError(f"Invalid expression: {exprs}")

        return result

    except BaseException as e:
        if activity.in_activity():
            activity.logger.error(f"Error in base_evaluate: {e}")
        newException = EvaluateError(e, chosen_expression, values)
        raise newException from e


# Note: This is here just for clarity. We could have just imported base_evaluate directly
# They do the same thing, so we dont need to mock the base_evaluate function
mock_base_evaluate = base_evaluate

base_evaluate = activity.defn(name="base_evaluate")(
    base_evaluate if not testing else mock_base_evaluate
)
