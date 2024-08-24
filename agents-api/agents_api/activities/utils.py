import json
from typing import Any

import re2
import yaml
from beartype import beartype
from simpleeval import EvalWithCompoundTypes, SimpleEval
from yaml import CSafeLoader

ALLOWED_FUNCTIONS = {
    "len": len,
    "load_yaml": lambda string: yaml.load(string, Loader=CSafeLoader),
    "match_regex": lambda pattern, string: bool(re2.fullmatch(pattern, string)),
    "search_regex": lambda pattern, string: re2.search(pattern, string),
    "load_json": json.loads,
}

@beartype
def get_evaluator(names: dict[str, Any]) -> SimpleEval:
    evaluator = EvalWithCompoundTypes(names=names, functions=ALLOWED_FUNCTIONS)
    return evaluator


@beartype
def simple_eval_dict(exprs: dict[str, str], values: dict[str, Any]) -> dict[str, Any]:
    evaluator = get_evaluator(names=values)

    return {k: evaluator.eval(v) for k, v in exprs.items()}
