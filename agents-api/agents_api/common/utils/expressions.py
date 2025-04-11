import ast
from typing import Any

import simpleeval
from beartype import beartype
from box import Box
from openai import BaseModel

# Increase the max string length to 2048000
simpleeval.MAX_STRING_LENGTH = 2048000

MAX_COLLECTION_SIZE = 1000  # Maximum number of variables allowed in evaluator

from simpleeval import SimpleEval
from temporalio import activity

from ..exceptions.executions import EvaluateError
from ..utils.task_validation import backwards_compatibility
from .evaluator import get_evaluator


# Recursive evaluation helper function
def _recursive_evaluate(expr, evaluator: SimpleEval):
    # Handle PyExpression type from the model
    if hasattr(expr, "root") and isinstance(expr.root, str):
        # Extract the string from the RootModel
        expr = expr.root

    if isinstance(expr, str):
        try:
            expr = backwards_compatibility(expr)
            expr = expr.strip()
            if isinstance(expr, str) and expr.startswith("$ "):
                # Remove $ and any space after it
                expr = expr[1:].strip()
            else:
                expr = f"f'''{expr}'''"
            return evaluator.eval(expr)
        except Exception as e:
            evaluate_error = EvaluateError(e, expr, evaluator.names)
            if activity.in_activity():
                activity.logger.error(f"Error in base_evaluate: {evaluate_error}\n")
            raise evaluate_error from e
    elif isinstance(expr, int | bool | float):
        return expr
    elif isinstance(expr, list):
        return [_recursive_evaluate(e, evaluator) for e in expr]
    elif isinstance(expr, dict):
        return {k: _recursive_evaluate(v, evaluator) for k, v in expr.items()}
    else:
        msg = f"Invalid expression: {expr}"
        raise ValueError(msg)


@beartype
def evaluate_expressions(
    exprs: Any,
    values: dict[str, Any] | None = None,
    extra_lambda_strs: dict[str, str] | None = None,
) -> Any | list[Any] | dict[str, Any]:
    # Handle PyExpression objects and strings similarly
    if isinstance(exprs, str) or (hasattr(exprs, "root") and isinstance(exprs.root, str)):
        input_len = 1
    else:
        input_len = len(exprs)

    assert input_len > 0, "exprs must be a non-empty string, PyExpression, list or dict"

    extra_lambdas = {}
    if extra_lambda_strs:
        for k, v in extra_lambda_strs.items():
            v = v.strip()

            # Check that all extra lambdas are valid
            assert v.startswith("lambda "), "All extra lambdas must start with 'lambda'"

            try:
                ast.parse(v)
            except Exception as e:
                msg = f"Invalid lambda: {v}"
                raise ValueError(msg) from e

            # Eval the lambda and add it to the extra lambdas
            extra_lambdas[k] = eval(v)

    # Turn the nested dict values from pydantic to dicts where possible
    values = {k: v.model_dump() if isinstance(v, BaseModel) else v for k, v in values.items()}

    # frozen_box doesn't work coz we need some mutability in the values
    values = Box(values, frozen_box=False, conversion_box=True)

    evaluator: SimpleEval = get_evaluator(names=values, extra_functions=extra_lambdas)

    # Recursively evaluate the expression
    return _recursive_evaluate(exprs, evaluator)
