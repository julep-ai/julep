import json
import traceback
from typing import Any

import wit_world


class WitWorld(wit_world.WitWorld):
    def run(self, request: str) -> str:
        try:
            payload = json.loads(request)
            source = payload["source"]
            func_name = payload["func"]
            value = payload.get("value")
            static_args = payload.get("static_args") or {}
            if not isinstance(source, str):
                raise TypeError("source must be a string")
            if not isinstance(func_name, str):
                raise TypeError("func must be a string")
            if not isinstance(static_args, dict):
                raise TypeError("static_args must be an object")

            namespace: dict[str, Any] = {"__builtins__": __builtins__}
            exec(source, namespace, namespace)
            func = namespace[func_name]
            result = func(value, **static_args)
            response = {"ok": True, "value": result}
        except Exception as exc:
            response = {
                "ok": False,
                "error": str(exc),
                "error_type": type(exc).__name__,
                "traceback_tail": traceback.format_exc(limit=2).splitlines()[-3:],
            }
        return json.dumps(response, sort_keys=True, separators=(",", ":"))
