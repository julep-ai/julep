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

from ..autogen.openapi_model import SystemDef
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
    "dump_json": json.dumps,
    "dump_yaml": yaml.dump,
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

constants = {
    "NEWLINE": "\n",
    "true": True,
    "false": False,
    "null": None,
}


@beartype
def get_evaluator(
    names: dict[str, Any], extra_functions: dict[str, Callable] | None = None
) -> SimpleEval:
    evaluator = EvalWithCompoundTypes(
        names=names | stdlib | constants,
        functions=ALLOWED_FUNCTIONS | (extra_functions or {}),
    )

    return evaluator


@beartype
def simple_eval_dict(exprs: dict[str, str], values: dict[str, Any]) -> dict[str, Any]:
    evaluator = get_evaluator(names=values)

    return {k: evaluator.eval(v) for k, v in exprs.items()}


def get_handler_with_filtered_params(system: SystemDef) -> Callable:
    """
    Get the appropriate handler function based on the SystemDef.

    Parameters:
        system (SystemDef): The system definition to get the handler for.

    Returns:
        A wrapped handler function with problematic parameters filtered out
        from its signature for JSON schema serialization.
    """

    from functools import wraps
    from inspect import signature

    # Get the base handler based on system definition
    base_handler = get_handler(system)

    # Skip parameters that can't be serialized to JSON schema
    parameters_to_exclude = ["background_tasks"]

    # Get the original signature
    sig = signature(base_handler)

    # Create a new function with filtered parameters
    @wraps(base_handler)
    def filtered_handler(*args, **kwargs):
        return base_handler(*args, **kwargs)

    # Remove problematic parameters
    filtered_handler.__signature__ = sig.replace(
        parameters=[
            p for p in sig.parameters.values() if p.name not in parameters_to_exclude
        ]
    )

    return filtered_handler


def get_handler(system: SystemDef) -> Callable:
    """
    Internal function to get the base handler without parameter filtering.

    Parameters:
        system (SystemDef): The system definition to get the handler for.

    Returns:
        The base handler function.
    """

    from ..models.agent.create_agent import create_agent as create_agent_query
    from ..models.agent.delete_agent import delete_agent as delete_agent_query
    from ..models.agent.get_agent import get_agent as get_agent_query
    from ..models.agent.list_agents import list_agents as list_agents_query
    from ..models.agent.update_agent import update_agent as update_agent_query
    from ..models.docs.delete_doc import delete_doc as delete_doc_query
    from ..models.docs.list_docs import list_docs as list_docs_query
    from ..models.session.create_session import create_session as create_session_query
    from ..models.session.delete_session import delete_session as delete_session_query
    from ..models.session.get_session import get_session as get_session_query
    from ..models.session.list_sessions import list_sessions as list_sessions_query
    from ..models.session.update_session import update_session as update_session_query
    from ..models.task.create_task import create_task as create_task_query
    from ..models.task.delete_task import delete_task as delete_task_query
    from ..models.task.get_task import get_task as get_task_query
    from ..models.task.list_tasks import list_tasks as list_tasks_query
    from ..models.task.update_task import update_task as update_task_query
    from ..models.user.create_user import create_user as create_user_query
    from ..models.user.delete_user import delete_user as delete_user_query
    from ..models.user.get_user import get_user as get_user_query
    from ..models.user.list_users import list_users as list_users_query
    from ..models.user.update_user import update_user as update_user_query
    from ..routers.docs.create_doc import create_agent_doc, create_user_doc
    from ..routers.docs.search_docs import search_agent_docs, search_user_docs
    from ..routers.sessions.chat import chat

    match (system.resource, system.subresource, system.operation):
        # AGENTS
        case ("agent", "doc", "list"):
            return list_docs_query
        case ("agent", "doc", "create"):
            return create_agent_doc
        case ("agent", "doc", "delete"):
            return delete_doc_query
        case ("agent", "doc", "search"):
            return search_agent_docs
        case ("agent", None, "list"):
            return list_agents_query
        case ("agent", None, "get"):
            return get_agent_query
        case ("agent", None, "create"):
            return create_agent_query
        case ("agent", None, "update"):
            return update_agent_query
        case ("agent", None, "delete"):
            return delete_agent_query

        # USERS
        case ("user", "doc", "list"):
            return list_docs_query
        case ("user", "doc", "create"):
            return create_user_doc
        case ("user", "doc", "delete"):
            return delete_doc_query
        case ("user", "doc", "search"):
            return search_user_docs
        case ("user", None, "list"):
            return list_users_query
        case ("user", None, "get"):
            return get_user_query
        case ("user", None, "create"):
            return create_user_query
        case ("user", None, "update"):
            return update_user_query
        case ("user", None, "delete"):
            return delete_user_query

        # SESSIONS
        case ("session", None, "list"):
            return list_sessions_query
        case ("session", None, "get"):
            return get_session_query
        case ("session", None, "create"):
            return create_session_query
        case ("session", None, "update"):
            return update_session_query
        case ("session", None, "delete"):
            return delete_session_query
        case ("session", None, "chat"):
            return chat

        # TASKS
        case ("task", None, "list"):
            return list_tasks_query
        case ("task", None, "get"):
            return get_task_query
        case ("task", None, "create"):
            return create_task_query
        case ("task", None, "update"):
            return update_task_query
        case ("task", None, "delete"):
            return delete_task_query

        case _:
            raise NotImplementedError(
                f"System call not implemented for {system.resource}.{system.operation}"
            )
