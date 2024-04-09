# Base

[Julep Python SDK Index](../../README.md#julep-python-sdk-index) / [Julep](../index.md#julep) / [Managers](./index.md#managers) / Base

> Auto-generated documentation for [julep.managers.base](../../../../../../julep/managers/base.py) module.

- [Base](#base)
  - [BaseManager](#basemanager)

## BaseManager

[Show source in base.py:7](../../../../../../julep/managers/base.py#L7)

A class that serves as a base manager for working with different API clients.

Attributes:
    api_client (Union[JulepApi, AsyncJulepApi]): A client instance for communicating with an API.
        It can either be an instance of JulepApi for synchronous operations or
        AsyncJulepApi for asynchronous operations.

Args:
    api_client (Union[JulepApi, AsyncJulepApi]): The API client that is used for making API calls.

#### Signature

```python
class BaseManager:
    def __init__(self, api_client: Union[JulepApi, AsyncJulepApi]): ...
```