# ChatResponse

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / ChatResponse

> Auto-generated documentation for [julep.api.types.chat_response](../../../../../../../julep/api/types/chat_response.py) module.

- [ChatResponse](#chatresponse)
  - [ChatResponse](#chatresponse-1)

## ChatResponse

[Show source in chat_response.py:18](../../../../../../../julep/api/types/chat_response.py#L18)

Represents a chat completion response returned by model, based on the provided input.

#### Signature

```python
class ChatResponse(pydantic.BaseModel): ...
```

### ChatResponse().dict

[Show source in chat_response.py:44](../../../../../../../julep/api/types/chat_response.py#L44)

#### Signature

```python
def dict(self, **kwargs: typing.Any) -> typing.Dict[str, typing.Any]: ...
```

### ChatResponse().json

[Show source in chat_response.py:36](../../../../../../../julep/api/types/chat_response.py#L36)

#### Signature

```python
def json(self, **kwargs: typing.Any) -> str: ...
```