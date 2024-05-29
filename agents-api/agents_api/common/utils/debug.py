from functools import wraps


def pdb_on_exception(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            import pdb
            import traceback

            traceback.print_exc()
            pdb.set_trace()
            raise

    return wrapper
