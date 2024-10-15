import base64
import datetime as dt
import functools
import itertools
import json
import math
import random
import statistics
import string
import time
import urllib.parse
from typing import Any, Callable, ParamSpec, TypeVar

import re2
import zoneinfo
from beartype import beartype
from simpleeval import EvalWithCompoundTypes, SimpleEval

from ..common.utils import yaml

T = TypeVar("T")
R = TypeVar("R")
P = ParamSpec("P")


# TODO: We need to make sure that we dont expose any security issues
ALLOWED_FUNCTIONS = {
    "abs": abs,
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
    "map": map,
    "max": max,
    "min": min,
    "range": range,
    "round": round,
    "set": set,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "reduce": functools.reduce,
    "zip": zip,
    "search_regex": lambda pattern, string: re2.search(pattern, string),
    "load_json": json.loads,
    "load_yaml": yaml.load,
    "match_regex": lambda pattern, string: bool(re2.fullmatch(pattern, string)),
}


class stdlib_re:
    fullmatch = re2.fullmatch
    search = re2.search
    escape = re2.escape
    findall = re2.findall
    finditer = re2.finditer
    match = re2.match
    split = re2.split
    sub = re2.sub
    subn = re2.subn


class stdlib_json:
    loads = json.loads
    dumps = json.dumps


class stdlib_yaml:
    load = yaml.load
    dump = yaml.dump


class stdlib_time:
    strftime = time.strftime
    strptime = time.strptime
    time = time


class stdlib_random:
    choice = random.choice
    choices = random.choices
    sample = random.sample
    shuffle = random.shuffle
    randrange = random.randrange
    randint = random.randint
    random = random.random


class stdlib_itertools:
    accumulate = itertools.accumulate


class stdlib_functools:
    partial = functools.partial
    reduce = functools.reduce


class stdlib_base64:
    b64encode = base64.b64encode
    b64decode = base64.b64decode


class stdlib_urllib:
    class parse:
        urlparse = urllib.parse.urlparse
        urlencode = urllib.parse.urlencode
        unquote = urllib.parse.unquote
        quote = urllib.parse.quote
        parse_qs = urllib.parse.parse_qs
        parse_qsl = urllib.parse.parse_qsl
        urlsplit = urllib.parse.urlsplit
        urljoin = urllib.parse.urljoin
        unwrap = urllib.parse.unwrap


class stdlib_string:
    ascii_letters = string.ascii_letters
    ascii_lowercase = string.ascii_lowercase
    ascii_uppercase = string.ascii_uppercase
    digits = string.digits
    hexdigits = string.hexdigits
    octdigits = string.octdigits
    punctuation = string.punctuation
    whitespace = string.whitespace
    printable = string.printable


class stdlib_zoneinfo:
    ZoneInfo = zoneinfo.ZoneInfo


class stdlib_datetime:
    class timezone:
        class utc:
            utc = dt.timezone.utc

    class datetime:
        now = dt.datetime.now
        datetime = dt.datetime
        timedelta = dt.timedelta
        date = dt.date
        time = dt.time

    timedelta = dt.timedelta


class stdlib_math:
    sqrt = math.sqrt
    exp = math.exp
    ceil = math.ceil
    floor = math.floor
    isinf = math.isinf
    isnan = math.isnan
    log = math.log
    log10 = math.log10
    log2 = math.log2
    pow = math.pow
    sin = math.sin
    cos = math.cos
    tan = math.tan
    asin = math.asin
    acos = math.acos
    atan = math.atan
    atan2 = math.atan2

    pi = math.pi
    e = math.e


class stdlib_statistics:
    mean = statistics.mean
    stdev = statistics.stdev
    geometric_mean = statistics.geometric_mean
    median = statistics.median
    median_low = statistics.median_low
    median_high = statistics.median_high
    mode = statistics.mode
    quantiles = statistics.quantiles


stdlib = {
    "re": stdlib_re,
    "json": stdlib_json,
    "yaml": stdlib_yaml,
    "time": stdlib_time,
    "random": stdlib_random,
    "itertools": stdlib_itertools,
    "functools": stdlib_functools,
    "base64": stdlib_base64,
    "urllib": stdlib_urllib,
    "string": stdlib_string,
    "zoneinfo": stdlib_zoneinfo,
    "datetime": stdlib_datetime,
    "math": stdlib_math,
    "statistics": stdlib_statistics,
}


@beartype
def get_evaluator(
    names: dict[str, Any], extra_functions: dict[str, Callable] | None = None
) -> SimpleEval:
    evaluator = EvalWithCompoundTypes(
        names=names | stdlib, functions=ALLOWED_FUNCTIONS | (extra_functions or {})
    )

    return evaluator


@beartype
def simple_eval_dict(exprs: dict[str, str], values: dict[str, Any]) -> dict[str, Any]:
    evaluator = get_evaluator(names=values)

    return {k: evaluator.eval(v) for k, v in exprs.items()}
