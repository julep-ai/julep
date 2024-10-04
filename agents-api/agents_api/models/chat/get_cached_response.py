from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def get_cached_response(key: str) -> tuple[str, dict]:
    query = """
        input[key] <- [[$key]]
        ?[key, value] := input[key], *session_cache{key, value}
        :limit 1
    """

    return (query, {"key": key})
