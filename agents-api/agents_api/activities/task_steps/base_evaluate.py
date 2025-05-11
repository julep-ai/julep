# AIDEV-NOTE: This module provides the activity for evaluating Python expressions within the task execution context.
from typing import Any

from beartype import beartype
from simpleeval import SimpleEval
from temporalio import activity

from ...common.exceptions.executions import EvaluateError
from ...common.protocol.tasks import StepContext
from ...common.utils.expressions import evaluate_expressions
from ...common.utils.task_validation import backwards_compatibility


# AIDEV-NOTE: Recursively evaluates expressions, handling different data types (strings, lists, dicts) and PyExpression objects.
# It prepares the expression for evaluation by the simpleeval library.
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


# AIDEV-NOTE: Main activity function for evaluating expressions.
# Sets up the evaluation environment with context values and extra functions, then calls the recursive evaluator.
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
        # NOTE: We limit the number of inputs to 50 to avoid excessive memory usage
        values.update(await context.prepare_for_step(limit=50))

    return evaluate_expressions(exprs, values=values, extra_lambda_strs=extra_lambda_strs)
