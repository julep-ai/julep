# ChatMultipleChatOutput

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Julep Python Library](../index.md#julep-python-library) / [Types](./index.md#types) / ChatMultipleChatOutput

> Auto-generated documentation for [julep.api.types.chat_multiple_chat_output](../../../../../../../julep/api/types/chat_multiple_chat_output.py) module.

- [ChatMultipleChatOutput](#chatmultiplechatoutput)
  - [ChatMultipleChatOutput](#chatmultiplechatoutput-1)

## ChatMultipleChatOutput

[Show source in chat_multiple_chat_output.py:12](../../../../../../../julep/api/types/chat_multiple_chat_output.py#L12)

The output returned by the model. Note that, depending on the model provider, they might return more than one message.

#### Signature

```python
class ChatMultipleChatOutput(ChatBaseChatOutput): ...
```

### ChatMultipleChatOutput().dict

[Show source in chat_multiple_chat_output.py:27](../../../../../../../julep/api/types/chat_multiple_chat_output.py#L27)

#### Signature

```python
def dict(self, **kwargs: typing.Any) -> typing.Dict[str, typing.Any]: ...
```

### ChatMultipleChatOutput().json

[Show source in chat_multiple_chat_output.py:19](../../../../../../../julep/api/types/chat_multiple_chat_output.py#L19)

#### Signature

```python
def json(self, **kwargs: typing.Any) -> str: ...
```