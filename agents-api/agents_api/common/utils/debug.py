from functools import wraps


def breakpoint_on_exception(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            import traceback

            print("Exception:")
            print("-" * 80)
            print(repr(getattr(exc, "__cause__", exc)))
            print("-" * 80)
            print()
            print("Traceback:")
            traceback.print_exc()

            breakpoint()
            raise

    return wrapper
