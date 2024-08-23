from typing import Any

from beartype import beartype
from temporalio import activity

from ...env import testing
from ..utils import get_evaluator


@beartype
async def base_evaluate(
    exprs: str | list[str] | dict[str, str],
    values: dict[str, Any] = {},
) -> Any | list[Any] | dict[str, Any]:
    input_len = 1 if isinstance(exprs, str) else len(exprs)
    assert input_len > 0, "exprs must be a non-empty string, list or dict"

    evaluator = get_evaluator(names=values)

    try:
        match exprs:
            case str():
                return evaluator.eval(exprs)

            case list():
                return [evaluator.eval(expr) for expr in exprs]

            case dict():
                return {k: evaluator.eval(v) for k, v in exprs.items()}

    except BaseException as e:
        if activity.in_activity():
            activity.logger.error(f"Error in base_evaluate: {e}")

        raise


# Note: This is here just for clarity. We could have just imported base_evaluate directly
# They do the same thing, so we dont need to mock the base_evaluate function
mock_base_evaluate = base_evaluate

base_evaluate = activity.defn(name="base_evaluate")(
    base_evaluate if not testing else mock_base_evaluate
)
