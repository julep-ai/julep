from ..utils import cozo_query

from beartype import beartype


@cozo_query
@beartype
def get_cached_response(key: str) -> tuple[str, dict]:
    query = """
        input[key] <- [[$key]]
        ?[key, value] := input[key], *session_cache{key, value}
    """

    return (query, {"key": key})
