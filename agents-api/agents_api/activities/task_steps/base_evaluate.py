import ast
from typing import Any

import simpleeval
from beartype import beartype
from box import Box
from openai import BaseModel

# Increase the max string length to 2048000
simpleeval.MAX_STRING_LENGTH = 2048000

from simpleeval import SimpleEval
from temporalio import activity

from ...common.protocol.tasks import StepContext
from ..utils import get_evaluator
from ...common.exceptions.executions import EvaluateError


# Recursive evaluation helper function
def _recursive_evaluate(expr, evaluator: SimpleEval):
    if isinstance(expr, str):
        try:
            if isinstance(expr, str) and expr.startswith("$ "):
                expr = expr[2:].strip()
            else:
                return expr
            return evaluator.eval(expr)
        except Exception as e:
            evaluate_error = EvaluateError(e, expr, evaluator.names)
            if activity.in_activity():
                activity.logger.error(f"Error in base_evaluate: {evaluate_error}\n")
            raise evaluate_error from e
    elif isinstance(expr, list):
        return [_recursive_evaluate(e, evaluator) for e in expr]
    elif isinstance(expr, dict):
        return {k: _recursive_evaluate(v, evaluator) for k, v in expr.items()}
    else:
        msg = f"Invalid expression: {expr}"
        raise ValueError(msg)


@activity.defn
@beartype
async def base_evaluate(
    exprs: Any,
    context: StepContext | None = None,
    values: dict[str, Any] | None = None,
    extra_lambda_strs: dict[str, str] | None = None,
) -> Any | list[Any] | dict[str, Any]:
    if context is None and values is None:
        msg = "Either context or values must be provided"
        raise ValueError(msg)

    values = values or {}
    if context:
        values.update(await context.prepare_for_step())

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
