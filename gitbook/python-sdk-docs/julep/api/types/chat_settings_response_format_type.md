# ChatSettingsResponseFormatType

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / ChatSettingsResponseFormatType

> Auto-generated documentation for [julep.api.types.chat_settings_response_format_type](../../../../../../../julep/api/types/chat_settings_response_format_type.py) module.

- [ChatSettingsResponseFormatType](#chatsettingsresponseformattype)
  - [ChatSettingsResponseFormatType](#chatsettingsresponseformattype-1)

## ChatSettingsResponseFormatType

[Show source in chat_settings_response_format_type.py:9](../../../../../../../julep/api/types/chat_settings_response_format_type.py#L9)

Must be one of `text` or `json_object`.

#### Signature

```python
class ChatSettingsResponseFormatType(str, enum.Enum): ...
```

### ChatSettingsResponseFormatType().visit

[Show source in chat_settings_response_format_type.py:17](../../../../../../../julep/api/types/chat_settings_response_format_type.py#L17)

#### Signature

```python
def visit(
    self, text: typing.Callable[[], T_Result], json_object: typing.Callable[[], T_Result]
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)