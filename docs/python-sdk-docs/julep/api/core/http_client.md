# HttpClient

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Julep Python Library](../index.md#julep-python-library) / [Core](./index.md#core) / HttpClient

> Auto-generated documentation for [julep.api.core.http_client](../../../../../../../julep/api/core/http_client.py) module.

- [HttpClient](#httpclient)
  - [AsyncHttpClient](#asynchttpclient)
  - [HttpClient](#httpclient-1)
  - [_parse_retry_after](#_parse_retry_after)
  - [_retry_timeout](#_retry_timeout)
  - [get_request_body](#get_request_body)
  - [maybe_filter_request_body](#maybe_filter_request_body)
  - [remove_omit_from_dict](#remove_omit_from_dict)

## AsyncHttpClient

[Show source in http_client.py:357](../../../../../../../julep/api/core/http_client.py#L357)

#### Signature

```python
class AsyncHttpClient:
    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        base_timeout: typing.Optional[float],
        base_headers: typing.Dict[str, str],
        base_url: typing.Optional[str] = None,
    ): ...
```

### AsyncHttpClient().get_base_url

[Show source in http_client.py:371](../../../../../../../julep/api/core/http_client.py#L371)

#### Signature

```python
def get_base_url(self, maybe_base_url: typing.Optional[str]) -> str: ...
```

### AsyncHttpClient().request

[Show source in http_client.py:379](../../../../../../../julep/api/core/http_client.py#L379)

#### Signature

```python
async def request(
    self,
    path: typing.Optional[str] = None,
    method: str,
    base_url: typing.Optional[str] = None,
    params: typing.Optional[typing.Dict[str, typing.Any]] = None,
    json: typing.Optional[typing.Any] = None,
    data: typing.Optional[typing.Any] = None,
    content: typing.Optional[
        typing.Union[bytes, typing.Iterator[bytes], typing.AsyncIterator[bytes]]
    ] = None,
    files: typing.Optional[
        typing.Dict[str, typing.Optional[typing.Union[File, typing.List[File]]]]
    ] = None,
    headers: typing.Optional[typing.Dict[str, typing.Any]] = None,
    request_options: typing.Optional[RequestOptions] = None,
    retries: int = 0,
    omit: typing.Optional[typing.Any] = None,
) -> httpx.Response: ...
```

### AsyncHttpClient().stream

[Show source in http_client.py:480](../../../../../../../julep/api/core/http_client.py#L480)

#### Signature

```python
@asynccontextmanager
async def stream(
    self,
    path: typing.Optional[str] = None,
    method: str,
    base_url: typing.Optional[str] = None,
    params: typing.Optional[typing.Dict[str, typing.Any]] = None,
    json: typing.Optional[typing.Any] = None,
    data: typing.Optional[typing.Any] = None,
    content: typing.Optional[
        typing.Union[bytes, typing.Iterator[bytes], typing.AsyncIterator[bytes]]
    ] = None,
    files: typing.Optional[
        typing.Dict[str, typing.Optional[typing.Union[File, typing.List[File]]]]
    ] = None,
    headers: typing.Optional[typing.Dict[str, typing.Any]] = None,
    request_options: typing.Optional[RequestOptions] = None,
    retries: int = 0,
    omit: typing.Optional[typing.Any] = None,
) -> typing.AsyncIterator[httpx.Response]: ...
```



## HttpClient

[Show source in http_client.py:153](../../../../../../../julep/api/core/http_client.py#L153)

#### Signature

```python
class HttpClient:
    def __init__(
        self,
        httpx_client: httpx.Client,
        base_timeout: typing.Optional[float],
        base_headers: typing.Dict[str, str],
        base_url: typing.Optional[str] = None,
    ): ...
```

### HttpClient().get_base_url

[Show source in http_client.py:167](../../../../../../../julep/api/core/http_client.py#L167)

#### Signature

```python
def get_base_url(self, maybe_base_url: typing.Optional[str]) -> str: ...
```

### HttpClient().request

[Show source in http_client.py:175](../../../../../../../julep/api/core/http_client.py#L175)

#### Signature

```python
def request(
    self,
    path: typing.Optional[str] = None,
    method: str,
    base_url: typing.Optional[str] = None,
    params: typing.Optional[typing.Dict[str, typing.Any]] = None,
    json: typing.Optional[typing.Any] = None,
    data: typing.Optional[typing.Any] = None,
    content: typing.Optional[
        typing.Union[bytes, typing.Iterator[bytes], typing.AsyncIterator[bytes]]
    ] = None,
    files: typing.Optional[
        typing.Dict[str, typing.Optional[typing.Union[File, typing.List[File]]]]
    ] = None,
    headers: typing.Optional[typing.Dict[str, typing.Any]] = None,
    request_options: typing.Optional[RequestOptions] = None,
    retries: int = 0,
    omit: typing.Optional[typing.Any] = None,
) -> httpx.Response: ...
```

### HttpClient().stream

[Show source in http_client.py:276](../../../../../../../julep/api/core/http_client.py#L276)

#### Signature

```python
@contextmanager
def stream(
    self,
    path: typing.Optional[str] = None,
    method: str,
    base_url: typing.Optional[str] = None,
    params: typing.Optional[typing.Dict[str, typing.Any]] = None,
    json: typing.Optional[typing.Any] = None,
    data: typing.Optional[typing.Any] = None,
    content: typing.Optional[
        typing.Union[bytes, typing.Iterator[bytes], typing.AsyncIterator[bytes]]
    ] = None,
    files: typing.Optional[
        typing.Dict[str, typing.Optional[typing.Union[File, typing.List[File]]]]
    ] = None,
    headers: typing.Optional[typing.Dict[str, typing.Any]] = None,
    request_options: typing.Optional[RequestOptions] = None,
    retries: int = 0,
    omit: typing.Optional[typing.Any] = None,
) -> typing.Iterator[httpx.Response]: ...
```



## _parse_retry_after

[Show source in http_client.py:26](../../../../../../../julep/api/core/http_client.py#L26)

This function parses the `Retry-After` header in a HTTP response and returns the number of seconds to wait.

Inspired by the urllib3 retry implementation.

#### Signature

```python
def _parse_retry_after(response_headers: httpx.Headers) -> typing.Optional[float]: ...
```



## _retry_timeout

[Show source in http_client.py:67](../../../../../../../julep/api/core/http_client.py#L67)

Determine the amount of time to wait before retrying a request.
This function begins by trying to parse a retry-after header from the response, and then proceeds to use exponential backoff
with a jitter to determine the number of seconds to wait.

#### Signature

```python
def _retry_timeout(response: httpx.Response, retries: int) -> float: ...
```



## get_request_body

[Show source in http_client.py:135](../../../../../../../julep/api/core/http_client.py#L135)

#### Signature

```python
def get_request_body(
    json: typing.Optional[typing.Any],
    data: typing.Optional[typing.Any],
    request_options: typing.Optional[RequestOptions],
    omit: typing.Optional[typing.Any],
) -> typing.Tuple[typing.Optional[typing.Any], typing.Optional[typing.Any]]: ...
```



## maybe_filter_request_body

[Show source in http_client.py:107](../../../../../../../julep/api/core/http_client.py#L107)

#### Signature

```python
def maybe_filter_request_body(
    data: typing.Optional[typing.Any],
    request_options: typing.Optional[RequestOptions],
    omit: typing.Optional[typing.Any],
) -> typing.Optional[typing.Any]: ...
```



## remove_omit_from_dict

[Show source in http_client.py:94](../../../../../../../julep/api/core/http_client.py#L94)

#### Signature

```python
def remove_omit_from_dict(
    original: typing.Dict[str, typing.Optional[typing.Any]],
    omit: typing.Optional[typing.Any],
) -> typing.Dict[str, typing.Any]: ...
```