# ApiError

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Julep Python Library](../index.md#julep-python-library) / [Core](./index.md#core) / ApiError

> Auto-generated documentation for [julep.api.core.api_error](../../../../../../../julep/api/core/api_error.py) module.

- [ApiError](#apierror)
  - [ApiError](#apierror-1)

## ApiError

[Show source in api_error.py:6](../../../../../../../julep/api/core/api_error.py#L6)

#### Signature

```python
class ApiError(Exception):
    def __init__(
        self, status_code: typing.Optional[int] = None, body: typing.Any = None
    ): ...
```