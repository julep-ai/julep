import inspect
import re
from functools import partialmethod, wraps
from typing import Any, Callable, ParamSpec, Type, TypeVar
from uuid import UUID

import pandas as pd
from pydantic import BaseModel

from ..common.utils.cozo import uuid_int_list_to_uuid4
from ..env import do_verify_developer, do_verify_developer_owns_resource

P = ParamSpec("P")
T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=BaseModel)


def fix_uuid(
    item: dict[str, Any], attr_regex: str = r"^(?:id|.*_id)$"
) -> dict[str, Any]:
    # find the attributes that are ids
    id_attrs = [
        attr for attr in item.keys() if re.match(attr_regex, attr) and item[attr]
    ]

    if not id_attrs:
        return item

    fixed = {
        **item,
        **{
            attr: uuid_int_list_to_uuid4(item[attr])
            for attr in id_attrs
            if isinstance(item[attr], list)
        },
    }

    return fixed


def fix_uuid_list(
    items: list[dict[str, Any]], attr_regex: str = r"^(?:id|.*_id)$"
) -> list[dict[str, Any]]:
    fixed = list(map(lambda item: fix_uuid(item, attr_regex), items))
    return fixed


def fix_uuid_if_present(item: Any, attr_regex: str = r"^(?:id|.*_id)$") -> Any:
    match item:
        case [dict(), *_]:
            return fix_uuid_list(item, attr_regex)

        case dict():
            return fix_uuid(item, attr_regex)

        case _:
            return item


def partialclass(cls, *args, **kwargs):
    cls_signature = inspect.signature(cls)
    bound = cls_signature.bind_partial(*args, **kwargs)

    # The `updated=()` argument is necessary to avoid a TypeError when using @wraps for a class
    @wraps(cls, updated=())
    class NewCls(cls):
        __init__ = partialmethod(cls.__init__, *bound.args, **bound.kwargs)

    return NewCls


def mark_session_updated_query(developer_id: UUID | str, session_id: UUID | str) -> str:
    return f"""
    input[developer_id, session_id] <- [[
        to_uuid("{str(developer_id)}"),
        to_uuid("{str(session_id)}"),
    ]]

    ?[
        developer_id, 
        session_id,
        situation,
        summary,
        created_at,
        metadata,
        render_templates,
        token_budget,
        context_overflow,
        updated_at,
    ] :=
        input[developer_id, session_id],
        *sessions {{
            session_id,
            situation,
            summary,
            created_at,
            metadata,
            render_templates,
            token_budget,
            context_overflow,
            @ 'END'
        }},
        updated_at = [floor(now()), true]

    :put sessions {{
        developer_id,
        session_id,
        situation,
        summary,
        created_at,
        metadata,
        render_templates,
        token_budget,
        context_overflow,
        updated_at,
    }}
    """


def verify_developer_id_query(developer_id: UUID | str) -> str:
    if not do_verify_developer:
        return "?[exists] := exists = true"

    return f"""
    matched[count(developer_id)] :=
        *developers{{
            developer_id,
        }}, developer_id = to_uuid("{str(developer_id)}")
        
    ?[exists] :=
        matched[num],
        exists = num > 0,
        assert(exists, "Developer does not exist")

    :limit 1
    """


def verify_developer_owns_resource_query(
    developer_id: UUID | str,
    resource: str,
    parents: list[tuple[str, str]] | None = None,
    **resource_id,
) -> str:
    if not do_verify_developer_owns_resource:
        return "?[exists] := exists = true"

    parents = parents or []
    resource_id_key, resource_id_value = next(iter(resource_id.items()))

    parents.append((resource, resource_id_key))
    parent_keys = ["developer_id", *map(lambda x: x[1], parents)]

    rule_head = f"""
    found[count({resource_id_key})] :=
        developer_id = to_uuid("{str(developer_id)}"),
        {resource_id_key} = to_uuid("{str(resource_id_value)}"),
    """

    rule_body = ""
    for parent_key, (relation, key) in zip(parent_keys, parents):
        rule_body += f"""
        *{relation}{{
            {parent_key},
            {key},
        }},
        """

    assertion = f"""
    ?[exists] :=
        found[num],
        exists = num > 0,
        assert(exists, "Developer does not own resource {resource} with {resource_id_key} {resource_id_value}")

    :limit 1
    """

    rule = rule_head + rule_body + assertion
    return rule


def make_cozo_json_query(fields):
    return ", ".join(f'"{field}": {field}' for field in fields).strip()


def cozo_query(
    func: Callable[P, tuple[str | list[str | None], dict]] | None = None,
    debug: bool | None = None,
):
    def cozo_query_dec(func: Callable[P, tuple[str | list[Any], dict]]):
        """
        Decorator that wraps a function that takes arbitrary arguments, and
        returns a (query string, variables) tuple.

        The wrapped function should additionally take a client keyword argument
        and then run the query using the client, returning a DataFrame.
        """

        from pprint import pprint

        @wraps(func)
        def wrapper(*args: P.args, client=None, **kwargs: P.kwargs) -> pd.DataFrame:
            queries, variables = func(*args, **kwargs)

            if isinstance(queries, str):
                query = queries
            else:
                queries = [str(query) for query in queries if query]
                query = "}\n\n{\n".join(queries)
                query = f"{{ {query} }}"

            debug and print(query)
            debug and pprint(
                dict(
                    variables=variables,
                )
            )

            # Run the query
            from ..clients import cozo

            try:
                client = client or cozo.get_cozo_client()
                result = client.run(query, variables)

            except Exception as e:
                debug and print(repr(getattr(e, "__cause__", None) or e))
                raise

            # Need to fix the UUIDs in the result
            result = result.map(fix_uuid_if_present)

            debug and pprint(
                dict(
                    result=result.to_dict(orient="records"),
                )
            )

            return result

        # Set the wrapped function as an attribute of the wrapper,
        # forwards the __wrapped__ attribute if it exists.
        setattr(wrapper, "__wrapped__", getattr(func, "__wrapped__", func))

        return wrapper

    if func is not None and callable(func):
        return cozo_query_dec(func)

    return cozo_query_dec


def wrap_in_class(
    cls: Type[ModelT] | Callable[..., ModelT],
    one: bool = False,
    transform: Callable[[dict], dict] | None = None,
    _kind: str | None = None,
):
    def decorator(func: Callable[P, pd.DataFrame]):
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> ModelT | list[ModelT]:
            df = func(*args, **kwargs)

            # Convert df to list of dicts
            if _kind:
                df = df[df["_kind"] == _kind]

            data = df.to_dict(orient="records")

            nonlocal transform
            transform = transform or (lambda x: x)

            if one:
                assert len(data) >= 1, "Expected one result, got none"
                obj: ModelT = cls(**transform(data[0]))
                return obj

            objs: list[ModelT] = [cls(**item) for item in map(transform, data)]
            return objs

        # Set the wrapped function as an attribute of the wrapper,
        # forwards the __wrapped__ attribute if it exists.
        setattr(wrapper, "__wrapped__", getattr(func, "__wrapped__", func))

        return wrapper

    return decorator


def rewrap_exceptions(
    mapping: dict[
        Type[BaseException] | Callable[[BaseException], bool],
        Type[BaseException] | Callable[[BaseException], BaseException],
    ],
    /,
):
    def decorator(func: Callable[P, T]):
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            nonlocal mapping

            try:
                result: T = func(*args, **kwargs)

            except BaseException as error:
                for check, transform in mapping.items():
                    should_catch = (
                        isinstance(error, check)
                        if isinstance(check, type)
                        else check(error)
                    )

                    if should_catch:
                        new_error = (
                            transform(str(error))
                            if isinstance(transform, type)
                            else transform(error)
                        )

                        setattr(new_error, "__cause__", error)

                        raise new_error from error

                raise

            return result

        # Set the wrapped function as an attribute of the wrapper,
        # forwards the __wrapped__ attribute if it exists.
        setattr(wrapper, "__wrapped__", getattr(func, "__wrapped__", func))

        return wrapper

    return decorator
