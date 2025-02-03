import asyncio
import base64
import csv
import datetime as dt
import json
import math
import random
import statistics
import string
import time
import urllib.parse
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from functools import reduce
from threading import Lock as ThreadLock
from typing import Any, ParamSpec, TypeVar

import re2
from beartype import beartype
from simpleeval import EvalWithCompoundTypes, SimpleEval

from ..autogen.openapi_model import SystemDef
from ..common.nlp import nlp
from ..common.utils import yaml

# Security limits
MAX_STRING_LENGTH = 1_000_000  # 1MB
MAX_COLLECTION_SIZE = 10_000
MAX_RANGE_SIZE = 1_000_000

T = TypeVar("T")
R = TypeVar("R")
P = ParamSpec("P")


def safe_range(*args):
    result = range(*args)
    if len(result) > MAX_RANGE_SIZE:
        msg = f"Range size exceeds maximum of {MAX_RANGE_SIZE}"
        raise ValueError(msg)
    return result


@beartype
def safe_json_loads(s: str) -> Any:
    """
    Safely load a JSON string with size limits.

    Args:
        s: JSON string to parse

    Returns:
        Parsed JSON data

    Raises:
        ValueError: If string exceeds size limit
    """
    if len(s) > MAX_STRING_LENGTH:
        msg = f"String exceeds maximum length of {MAX_STRING_LENGTH}"
        raise ValueError(msg)
    return json.loads(s)


@beartype
def safe_yaml_load(s: str) -> Any:
    """
    Safely load a YAML string with size limits.

    Args:
        s: YAML string to parse

    Returns:
        Parsed YAML data

    Raises:
        ValueError: If string exceeds size limit
    """
    if len(s) > MAX_STRING_LENGTH:
        msg = f"String exceeds maximum length of {MAX_STRING_LENGTH}"
        raise ValueError(msg)
    return yaml.load(s)


@beartype
def safe_base64_decode(s: str) -> str:
    """
    Safely decode a base64 string with size limits.

    Args:
        s: Base64 string to decode

    Returns:
        Decoded UTF-8 string

    Raises:
        ValueError: If string exceeds size limit or is invalid base64
    """
    if len(s) > MAX_STRING_LENGTH:
        msg = f"String exceeds maximum length of {MAX_STRING_LENGTH}"
        raise ValueError(msg)
    try:
        return base64.b64decode(s).decode("utf-8")
    except Exception as e:
        msg = f"Invalid base64 string: {e}"
        raise ValueError(msg)


@beartype
def safe_base64_encode(s: str) -> str:
    """
    Safely encode a string to base64 with size limits.

    Args:
        s: String to encode

    Returns:
        Base64 encoded string

    Raises:
        ValueError: If string exceeds size limit
    """
    if len(s) > MAX_STRING_LENGTH:
        msg = f"String exceeds maximum length of {MAX_STRING_LENGTH}"
        raise ValueError(msg)
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")


@beartype
def safe_random_choice(seq: list[Any] | tuple[Any, ...] | str) -> Any:
    """
    Safely choose a random element from a sequence with size limits.

    Args:
        seq: A sequence (list, tuple, or string) to choose from

    Returns:
        A randomly selected element

    Raises:
        ValueError: If sequence exceeds size limit
        TypeError: If input is not a valid sequence type
    """
    if len(seq) > MAX_COLLECTION_SIZE:
        msg = f"Sequence exceeds maximum size of {MAX_COLLECTION_SIZE}"
        raise ValueError(msg)
    return random.choice(seq)


@beartype
def safe_random_sample(population: list[T] | tuple[T, ...] | str, k: int) -> list[T]:
    """
    Safely sample k elements from a population with size limits.

    Args:
        population: A sequence to sample from
        k: Number of elements to sample

    Returns:
        A list containing k randomly selected elements

    Raises:
        ValueError: If population/sample size exceeds limits
        TypeError: If input is not a valid sequence type
    """
    if not isinstance(population, list | tuple | str):
        msg = "Expected a sequence (list, tuple, or string)"
        raise TypeError(msg)
    if len(population) > MAX_COLLECTION_SIZE:
        msg = f"Population exceeds maximum size of {MAX_COLLECTION_SIZE}"
        raise ValueError(msg)
    if k > MAX_COLLECTION_SIZE:
        msg = f"Sample size exceeds maximum of {MAX_COLLECTION_SIZE}"
        raise ValueError(msg)
    if k > len(population):
        msg = "Sample size cannot exceed population size"
        raise ValueError(msg)
    return random.sample(population, k)


@beartype
def chunk_doc(string: str) -> list[str]:
    """
    Chunk a string into sentences.

    Args:
        string: The text to chunk into sentences

    Returns:
        A list of sentence chunks

    Raises:
        ValueError: If string exceeds size limit
    """
    if len(string) > MAX_STRING_LENGTH:
        msg = f"String exceeds maximum length of {MAX_STRING_LENGTH}"
        raise ValueError(msg)
    doc = nlp(string)
    return [" ".join([sent.text for sent in chunk]) for chunk in doc._.chunks]


def safe_extract_json(string: str):
    if len(string) > MAX_STRING_LENGTH:
        msg = f"String exceeds maximum length of {MAX_STRING_LENGTH}"
        raise ValueError(msg)
    # Check if the string contains JSON code block markers
    if "```json" in string:
        extracted_string = string[
            string.find("```json") + 7 : string.find("```", string.find("```json") + 7)
        ]
    else:
        # If no markers, try to parse the whole string as JSON
        extracted_string = string
    return json.loads(extracted_string)


# Restricted set of allowed functions
ALLOWED_FUNCTIONS = {
    # Basic Python builtins
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "round": round,
    "set": set,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
    "reduce": reduce,
    # Safe versions of potentially dangerous functions
    "range": safe_range,
    "load_json": safe_json_loads,
    "load_yaml": safe_yaml_load,
    "dump_json": json.dumps,
    "dump_yaml": yaml.dump,
    "extract_json": safe_extract_json,
    # Regex and NLP functions (using re2 which is safe against ReDoS)
    "search_regex": lambda pattern, string: re2.search(pattern, string),
    "match_regex": lambda pattern, string: bool(re2.fullmatch(pattern, string)),
    "nlp": nlp.__call__,
    "chunk_doc": chunk_doc,
}


class stdlib_csv:
    reader = csv.reader
    writer = csv.writer
    register_dialect = csv.register_dialect
    unregister_dialect = csv.unregister_dialect
    get_dialect = csv.get_dialect
    list_dialects = csv.list_dialects
    field_size_limit = csv.field_size_limit
    DictReader = csv.DictReader
    DictWriter = csv.DictWriter
    Dialect = csv.Dialect
    excel = csv.excel
    excel_tab = csv.excel_tab
    unix_dialect = csv.unix_dialect
    Sniffer = csv.Sniffer
    QUOTE_ALL = csv.QUOTE_ALL
    QUOTE_MINIMAL = csv.QUOTE_MINIMAL
    QUOTE_NONNUMERIC = csv.QUOTE_NONNUMERIC
    QUOTE_NONE = csv.QUOTE_NONE
    QUOTE_NOTNULL = csv.QUOTE_NOTNULL
    QUOTE_STRINGS = csv.QUOTE_STRINGS
    Error = csv.Error


# Safe regex operations (using re2)
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


# Safe JSON operations
class stdlib_json:
    loads = safe_json_loads
    dumps = json.dumps


# Safe YAML operations
class stdlib_yaml:
    load = safe_yaml_load
    dump = yaml.dump
    safe_load = safe_yaml_load
    safe_dump = yaml.dump


# Safe string constants
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


# Safe datetime operations
class stdlib_datetime:
    class timezone:
        class utc:
            utc = dt.UTC

    class datetime:
        now = dt.datetime.now
        datetime = dt.datetime
        timedelta = dt.timedelta
        date = dt.date
        time = dt.time

    timedelta = dt.timedelta


# Safe math operations
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


# Safe statistics operations
class stdlib_statistics:
    mean = statistics.mean
    stdev = statistics.stdev
    geometric_mean = statistics.geometric_mean
    median = statistics.median
    median_low = statistics.median_low
    median_high = statistics.median_high
    mode = statistics.mode
    quantiles = statistics.quantiles


# Safe base64 operations
class stdlib_base64:
    b64encode = safe_base64_encode
    b64decode = safe_base64_decode


# Safe URL parsing operations
class stdlib_urllib:
    class parse:
        # Safe URL parsing operations that don't touch filesystem/network
        urlparse = urllib.parse.urlparse
        urlencode = urllib.parse.urlencode
        unquote = urllib.parse.unquote
        quote = urllib.parse.quote
        parse_qs = urllib.parse.parse_qs
        parse_qsl = urllib.parse.parse_qsl
        urlsplit = urllib.parse.urlsplit


# Safe random operations
class stdlib_random:
    # Limit to safe operations with bounded inputs
    choice = safe_random_choice
    sample = safe_random_sample
    # Safe bounded random number generators
    randint = random.randint  # Already bounded by integer limits
    random = random.random  # Always returns 0.0 to 1.0


# Safe time operations
class stdlib_time:
    # Time formatting/parsing operations
    strftime = time.strftime
    strptime = time.strptime
    # Current time (safe, no side effects)
    time = time.time


# Restricted stdlib with only safe operations
stdlib = {
    "re": stdlib_re,
    "json": stdlib_json,
    "yaml": stdlib_yaml,
    "string": stdlib_string,
    "datetime": stdlib_datetime,
    "math": stdlib_math,
    "statistics": stdlib_statistics,
    "base64": stdlib_base64,
    "urllib": stdlib_urllib,
    "random": stdlib_random,
    "time": stdlib_time,
    "csv": stdlib_csv,
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
    if len(names) > MAX_COLLECTION_SIZE:
        msg = f"Too many variables (max {MAX_COLLECTION_SIZE})"
        raise ValueError(msg)

    evaluator = EvalWithCompoundTypes(
        names=names | stdlib | constants,
        functions=ALLOWED_FUNCTIONS | (extra_functions or {}),
    )

    # Add maximum execution time
    evaluator.TIMEOUT = 1.0  # 1 second timeout

    return evaluator


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
        parameters=[p for p in sig.parameters.values() if p.name not in parameters_to_exclude]
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

    from ..queries.agents.create_agent import create_agent as create_agent_query
    from ..queries.agents.delete_agent import delete_agent as delete_agent_query
    from ..queries.agents.get_agent import get_agent as get_agent_query
    from ..queries.agents.list_agents import list_agents as list_agents_query
    from ..queries.agents.update_agent import update_agent as update_agent_query
    from ..queries.docs.delete_doc import delete_doc as delete_doc_query
    from ..queries.docs.list_docs import list_docs as list_docs_query
    from ..queries.entries.get_history import get_history as get_history_query
    from ..queries.sessions.create_session import create_session as create_session_query
    from ..queries.sessions.get_session import get_session as get_session_query
    from ..queries.sessions.list_sessions import list_sessions as list_sessions_query
    from ..queries.sessions.update_session import update_session as update_session_query
    from ..queries.tasks.create_task import create_task as create_task_query
    from ..queries.tasks.delete_task import delete_task as delete_task_query
    from ..queries.tasks.get_task import get_task as get_task_query
    from ..queries.tasks.list_tasks import list_tasks as list_tasks_query
    from ..queries.tasks.update_task import update_task as update_task_query
    from ..queries.users.create_user import create_user as create_user_query
    from ..queries.users.delete_user import delete_user as delete_user_query
    from ..queries.users.get_user import get_user as get_user_query
    from ..queries.users.list_users import list_users as list_users_query
    from ..queries.users.update_user import update_user as update_user_query

    # FIXME: Do not use routes directly;
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
        # TODO: Add support for create_or_update_session
        case ("session", None, "chat"):
            return chat
        case ("session", None, "history"):
            return get_history_query

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
            msg = f"System call not implemented for {system.resource}.{system.operation}"
            raise NotImplementedError(msg)


@dataclass
class RateLimiter:
    max_requests: int  # Maximum requests per minute
    window_size: int = 60  # Window size in seconds (1 minute)

    def __post_init__(self):
        self._requests = deque()
        self._lock = ThreadLock()  # Thread-safe lock
        self._async_lock = asyncio.Lock()  # Async-safe lock

    def _clean_old_requests(self):
        now = time.time()
        while self._requests and now - self._requests[0] > self.window_size:
            self._requests.popleft()

    async def acquire(self):
        async with self._async_lock:
            with self._lock:
                now = time.time()
                self._clean_old_requests()

                if len(self._requests) >= self.max_requests:
                    return False

                self._requests.append(now)
                return True

    @property
    def current_usage(self) -> int:
        """Return current number of requests in the window"""
        with self._lock:
            self._clean_old_requests()
            return len(self._requests)
