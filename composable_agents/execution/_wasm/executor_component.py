import json
import traceback

import wit_world


class WitWorld(wit_world.WitWorld):
    def run(self, request: str) -> str:
        try:
            payload = json.loads(request)
            source = payload["source"]
            name = payload["name"]
            value = payload.get("value")
            kwargs = payload.get("kwargs", {})
            if not isinstance(source, str):
                raise TypeError("source must be a string")
            if not isinstance(name, str):
                raise TypeError("name must be a string")
            if not isinstance(kwargs, dict):
                raise TypeError("kwargs must be an object")

            registered = {}

            def pure(pure_name, /):
                if not isinstance(pure_name, str):
                    fn = pure_name
                    registered[fn.__name__] = fn
                    return fn

                def deco(fn):
                    registered[pure_name] = fn
                    return fn

                return deco

            def renderer(rname, /):
                if not isinstance(rname, str):
                    fn = rname
                    registered[fn.__name__] = fn
                    return fn

                def deco(fn):
                    registered[rname] = fn
                    return fn

                return deco

            namespace = {"__builtins__": __builtins__, "pure": pure, "renderer": renderer}
            exec(compile(source, "<wasm-pure>", "exec"), namespace, namespace)
            fn = registered.get(name)
            if fn is None:
                fn = namespace.get(name)
            if fn is None:
                raise NameError(f"source did not register pure {name!r}")

            response = {"ok": True, "value": fn(value, **kwargs)}
        except Exception as exc:
            response = {
                "ok": False,
                "error": str(exc),
                "error_type": type(exc).__name__,
                "traceback_tail": _traceback_tail(exc),
            }
        return json.dumps(response, sort_keys=True, separators=(",", ":"))


def _traceback_tail(exc: BaseException) -> list:
    # Under --stub-wasi there is NO filesystem, so traceback.format_exc() traps:
    # it walks frames and reads their source files via linecache, which hits the
    # (trapping) WASI filesystem syscalls. Build a short tail WITHOUT any file
    # access: walk the traceback for code name + line number only, then append
    # the exception-only line (type + message; no source lookup). Wrap the whole
    # thing so a hostile pure can never make the error handler itself trap.
    try:
        frames = []
        tb = exc.__traceback__
        while tb is not None:
            code = tb.tb_frame.f_code
            frames.append(f"{code.co_filename}:{tb.tb_lineno} in {code.co_name}")
            tb = tb.tb_next
        only = "".join(traceback.format_exception_only(type(exc), exc)).splitlines()
        return (frames[-3:] + only)[-3:]
    except Exception:
        return [f"{type(exc).__name__}: {exc}"]
