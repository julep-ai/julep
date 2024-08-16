from typing import Any

from beartype import beartype
from simpleeval import simple_eval


@beartype
def simple_eval_dict(
    exprs: dict[str, str], *, values: dict[str, Any]
) -> dict[str, Any]:
    return {k: simple_eval(v, names=values) for k, v in exprs.items()}
