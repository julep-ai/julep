# Client Wrapper

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Julep Python Library](../index.md#julep-python-library) / [Core](./index.md#core) / Client Wrapper

> Auto-generated documentation for [julep.api.core.client_wrapper](../../../../../../../julep/api/core/client_wrapper.py) module.

- [Client Wrapper](#client-wrapper)
  - [AsyncClientWrapper](#asyncclientwrapper)
  - [BaseClientWrapper](#baseclientwrapper)
  - [SyncClientWrapper](#syncclientwrapper)

## AsyncClientWrapper

[Show source in client_wrapper.py:58](../../../../../../../julep/api/core/client_wrapper.py#L58)

#### Signature

```python
class AsyncClientWrapper(BaseClientWrapper):
    def __init__(
        self,
        auth_key: str,
        api_key: str,
        base_url: str,
        timeout: typing.Optional[float] = None,
        httpx_client: httpx.AsyncClient,
    ): ...
```

#### See also

- [BaseClientWrapper](#baseclientwrapper)



## BaseClientWrapper

[Show source in client_wrapper.py:10](../../../../../../../julep/api/core/client_wrapper.py#L10)

#### Signature

```python
class BaseClientWrapper:
    def __init__(
        self,
        auth_key: str,
        api_key: str,
        base_url: str,
        timeout: typing.Optional[float] = None,
    ): ...
```

### BaseClientWrapper().get_base_url

[Show source in client_wrapper.py:30](../../../../../../../julep/api/core/client_wrapper.py#L30)

#### Signature

```python
def get_base_url(self) -> str: ...
```

### BaseClientWrapper().get_headers

[Show source in client_wrapper.py:24](../../../../../../../julep/api/core/client_wrapper.py#L24)

#### Signature

```python
def get_headers(self) -> typing.Dict[str, str]: ...
```

### BaseClientWrapper().get_timeout

[Show source in client_wrapper.py:33](../../../../../../../julep/api/core/client_wrapper.py#L33)

#### Signature

```python
def get_timeout(self) -> typing.Optional[float]: ...
```



## SyncClientWrapper

[Show source in client_wrapper.py:37](../../../../../../../julep/api/core/client_wrapper.py#L37)

#### Signature

```python
class SyncClientWrapper(BaseClientWrapper):
    def __init__(
        self,
        auth_key: str,
        api_key: str,
        base_url: str,
        timeout: typing.Optional[float] = None,
        httpx_client: httpx.Client,
    ): ...
```

#### See also

- [BaseClientWrapper](#baseclientwrapper)