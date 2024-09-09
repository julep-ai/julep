import json
from functools import reduce
from itertools import accumulate
from random import random
from time import time
from typing import Any, Callable

import re2
import yaml
from beartype import beartype
from simpleeval import EvalWithCompoundTypes, SimpleEval
from yaml import CSafeLoader

# TODO: We need to make sure that we dont expose any security issues
ALLOWED_FUNCTIONS = {
    "abs": abs,
    "accumulate": accumulate,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "frozenset": frozenset,
    "int": int,
    "len": len,
    "list": list,
    "load_json": json.loads,
    "load_yaml": lambda string: yaml.load(string, Loader=CSafeLoader),
    "map": map,
    "match_regex": lambda pattern, string: bool(re2.fullmatch(pattern, string)),
    "max": max,
    "min": min,
    "random": random,
    "range": range,
    "reduce": reduce,
    "round": round,
    "search_regex": lambda pattern, string: re2.search(pattern, string),
    "set": set,
    "str": str,
    "sum": sum,
    "time": time,
    "tuple": tuple,
    "zip": zip,
}


@beartype
def get_evaluator(
    names: dict[str, Any], extra_functions: dict[str, Callable] | None = None
) -> SimpleEval:
    evaluator = EvalWithCompoundTypes(
        names=names, functions=ALLOWED_FUNCTIONS | (extra_functions or {})
    )

    return evaluator


@beartype
def simple_eval_dict(exprs: dict[str, str], values: dict[str, Any]) -> dict[str, Any]:
    evaluator = get_evaluator(names=values)

    return {k: evaluator.eval(v) for k, v in exprs.items()}
