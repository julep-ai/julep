# Base

[Julep Python SDK Index](../../README.md#julep-python-sdk-index) / [Julep](../index.md#julep) / [Managers](./index.md#managers) / Base

> Auto-generated documentation for [julep.managers.base](../../../../../../julep/managers/base.py) module.

- [Base](#base)
  - [BaseManager](#basemanager)

## BaseManager

[Show source in base.py:7](../../../../../../julep/managers/base.py#L7)

A class that serves as a base manager for working with different API clients. This class is responsible for abstracting the complexities of interacting with various API clients, providing a unified interface for higher-level components.

Attributes:
    api_client (Union[JulepApi, AsyncJulepApi]): A client instance for communicating with an API. This attribute is essential for enabling the class to perform API operations, whether they are synchronous or asynchronous.

Args:
    api_client (Union[JulepApi, AsyncJulepApi]): The API client that is used for making API calls. It is crucial for the operation of this class, allowing it to interact with the API effectively.

#### Signature

```python
class BaseManager:
    def __init__(self, api_client: Union[JulepApi, AsyncJulepApi]): ...
```