# Client Wrapper

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Core](./index.md#core) / Client Wrapper

> Auto-generated documentation for [julep.api.core.client_wrapper](../../../../../../../julep/api/core/client_wrapper.py) module.

- [Client Wrapper](#client-wrapper)
  - [AsyncClientWrapper](#asyncclientwrapper)
  - [BaseClientWrapper](#baseclientwrapper)
  - [SyncClientWrapper](#syncclientwrapper)

## AsyncClientWrapper

[Show source in client_wrapper.py:28](../../../../../../../julep/api/core/client_wrapper.py#L28)

#### Signature

```python
class AsyncClientWrapper(BaseClientWrapper):
    def __init__(self, api_key: str, base_url: str, httpx_client: httpx.AsyncClient): ...
```

#### See also

- [BaseClientWrapper](#baseclientwrapper)



## BaseClientWrapper

[Show source in client_wrapper.py:8](../../../../../../../julep/api/core/client_wrapper.py#L8)

#### Signature

```python
class BaseClientWrapper:
    def __init__(self, api_key: str, base_url: str): ...
```

### BaseClientWrapper().get_base_url

[Show source in client_wrapper.py:18](../../../../../../../julep/api/core/client_wrapper.py#L18)

#### Signature

```python
def get_base_url(self) -> str: ...
```

### BaseClientWrapper().get_headers

[Show source in client_wrapper.py:13](../../../../../../../julep/api/core/client_wrapper.py#L13)

#### Signature

```python
def get_headers(self) -> typing.Dict[str, str]: ...
```



## SyncClientWrapper

[Show source in client_wrapper.py:22](../../../../../../../julep/api/core/client_wrapper.py#L22)

#### Signature

```python
class SyncClientWrapper(BaseClientWrapper):
    def __init__(self, api_key: str, base_url: str, httpx_client: httpx.Client): ...
```

#### See also

- [BaseClientWrapper](#baseclientwrapper)