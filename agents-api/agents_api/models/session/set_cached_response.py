from ..utils import cozo_query


@cozo_query
def set_cached_response(key: str, value: dict) -> tuple[str, dict]:
    query = """
        ?[key, value] <- [[$key, $value]]
        
        :insert session_cache {
            key => value
        }

        :returning
    """

    return (query, {"key": key, "value": value})
