from typing import Any

from beartype import beartype
from simpleeval import EvalWithCompoundTypes, SimpleEval


@beartype
def get_evaluator(names: dict[str, Any]) -> SimpleEval:
    evaluator = EvalWithCompoundTypes(names=names)
    return evaluator


@beartype
def simple_eval_dict(exprs: dict[str, str], values: dict[str, Any]) -> dict[str, Any]:
    evaluator = get_evaluator(names=values)

    return {k: evaluator.eval(v) for k, v in exprs.items()}
