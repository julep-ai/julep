# ChatSettingsResponseFormat

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / ChatSettingsResponseFormat

> Auto-generated documentation for [julep.api.types.chat_settings_response_format](../../../../../../../julep/api/types/chat_settings_response_format.py) module.

- [ChatSettingsResponseFormat](#chatsettingsresponseformat)
  - [ChatSettingsResponseFormat](#chatsettingsresponseformat-1)

## ChatSettingsResponseFormat

[Show source in chat_settings_response_format.py:15](../../../../../../../julep/api/types/chat_settings_response_format.py#L15)

An object specifying the format that the model must output.

Setting to `{ "type": "json_object" }` enables JSON mode, which guarantees the message the model generates is valid JSON.

**Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly "stuck" request. Also note that the message content may be partially cut off if `finish_reason="length"`, which indicates the generation exceeded `max_tokens` or the conversation exceeded the max context length.

#### Signature

```python
class ChatSettingsResponseFormat(pydantic.BaseModel): ...
```

### ChatSettingsResponseFormat().dict

[Show source in chat_settings_response_format.py:36](../../../../../../../julep/api/types/chat_settings_response_format.py#L36)

#### Signature

```python
def dict(self, **kwargs: typing.Any) -> typing.Dict[str, typing.Any]: ...
```

### ChatSettingsResponseFormat().json

[Show source in chat_settings_response_format.py:28](../../../../../../../julep/api/types/chat_settings_response_format.py#L28)

#### Signature

```python
def json(self, **kwargs: typing.Any) -> str: ...
```