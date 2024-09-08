import json
import os
from functools import partial, wraps
from typing import TypeVar, Callable, Any, ParamSpec

from .sdk.client import AuthenticatedClient
import julep.sdk.api.default as ops
from .sdk import errors


# Need to get all files from ops module and import them
from importlib import import_module

# Get all the files from the ops module
ops_files = [
    file
    for file in os.listdir(ops.__file__.rstrip("__init__.py"))
    if file.endswith(".py") and file != "__init__.py"
]

# Import all the files
for file in ops_files:
    file_name = file[:-3]
    try:
        import_module(f"julep.sdk.api.default.{file_name}")
    except ImportError:
        breakpoint()
        raise

    setattr(ops, file_name, import_module(f"julep.sdk.api.default.{file_name}"))


T = TypeVar('T', bound=Callable[..., Any])

P = ParamSpec('P')
R = TypeVar('R')

def parse_response(fn: Callable[P, R]) -> Callable[P, dict[str, Any]]:
    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> dict[str, Any]:
        response = fn(*args, **kwargs)
        if response.status_code.is_client_error or response.status_code.is_server_error:
            raise errors.UnexpectedStatus(response.status_code, response.content)
        else:
            result = json.loads(response.content)
            return result  # type: ignore

    return wrapper


class JulepNamespace:
    def __init__(self, name: str, client: AuthenticatedClient):
        self.name = name
        self.client = client


class Julep:
    def __init__(self, *, api_key: str, base_url: str = "https://api.julep.ai/api", **client_kwargs):
        self.client = AuthenticatedClient(token=api_key, base_url=base_url, **client_kwargs)

        # Get a list of all the available operations (attributes of the ops object)
        op_names: list[str] = [attr for attr in dir(ops) if not attr.startswith("_") and "route" in attr]

        # These look like: agents_route_create / agents_route_list etc.
        # The conventions are:
        # - The first part of the name is the resource name (agents, chat, etc.)
        # - The second part of the name is the method (route_create, route_list, etc.)
        # - The `_route_` prefix can be omitted.

        # We want to create a method on the Julep class for each of these that proxies to the ops object
        # But also ensures that the first argument (self.client) is passed through

        namespaces, operations = list(zip(*[name.split("_route_") for name in op_names]))

        # Some namespaces have aliases
        # This is because the API is organized by resource, but the SDK is organized by namespace
        # And we want to allow the user to use the resource name as the namespace name
        namespace_aliases = {
            "agents_docs_search": "agents_docs",
            "user_docs_search": "user_docs",
            "execution_transitions": "transitions",
            "execution_transitions_stream": "transitions",
            "individual_docs": "docs",
            "job": "jobs",
            "task_executions": "executions",
            "tasks_create_or_update": "tasks",
        }

        # First let's add the namespaces to the Julep class as attributes
        for namespace in namespaces:
            namespace = namespace_aliases.get(namespace, namespace)
            if not hasattr(self, namespace):
                setattr(self, namespace, JulepNamespace(namespace, self.client))

        # Now let's add the operations to the Julep class as attributes
        async_prefix = {"a": "asyncio_detailed", "": "sync_detailed"}

        for prefix, async_op in async_prefix.items():
            for namespace, operation in zip(namespaces, operations):
                op = getattr(ops, f"{namespace}_route_{operation}")
                op = getattr(op, async_op)
                op = partial(op, client=self.client)
                op = parse_response(op)
                op_name = prefix + operation

                namespace = namespace_aliases.get(namespace, namespace)
                ns = getattr(self, namespace)

                if not hasattr(ns, op_name):
                    setattr(ns, op_name, op)