from ..utils import cozo_query

from beartype import beartype


@cozo_query
@beartype
def set_cached_response(key: str, value: dict) -> tuple[str, dict]:
    query = """
        ?[key, value] <- [[$key, $value]]
        
        :insert session_cache {
            key => value
        }

        :returning
    """

    return (query, {"key": key, "value": value})
