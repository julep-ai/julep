import json
from uuid import UUID
from typing import Any


class CustomJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        self._default_empty_value = kwargs.pop("default_empty_value")
        super().__init__(*args, **kwargs)

    def encode(self, o):
        return super().encode(self.default(o))

    def default(self, obj):
        if obj is None:
            return self._default_empty_value

        if isinstance(obj, UUID):
            return str(obj)

        return obj


def dumps(obj: Any, default_empty_value="", cls=None) -> str:
    return json.dumps(
        obj, cls=cls or CustomJSONEncoder, default_empty_value=default_empty_value
    )
