# RequestOptions

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Julep Python Library](../index.md#julep-python-library) / [Core](./index.md#core) / RequestOptions

> Auto-generated documentation for [julep.api.core.request_options](../../../../../../../julep/api/core/request_options.py) module.

- [RequestOptions](#requestoptions)
  - [RequestOptions](#requestoptions-1)

## RequestOptions

[Show source in request_options.py:11](../../../../../../../julep/api/core/request_options.py#L11)

Additional options for request-specific configuration when calling APIs via the SDK.
This is used primarily as an optional final parameter for service functions.

#### Attributes

- `-` *timeout_in_seconds* - int. The number of seconds to await an API call before timing out.

- `-` *max_retries* - int. The max number of retries to attempt if the API call fails.

- `-` *additional_headers* - typing.Dict[str, typing.Any]. A dictionary containing additional parameters to spread into the request's header dict

- `-` *additional_query_parameters* - typing.Dict[str, typing.Any]. A dictionary containing additional parameters to spread into the request's query parameters dict

- `-` *additional_body_parameters* - typing.Dict[str, typing.Any]. A dictionary containing additional parameters to spread into the request's body parameters dict

#### Signature

```python
class RequestOptions(typing.TypedDict): ...
```