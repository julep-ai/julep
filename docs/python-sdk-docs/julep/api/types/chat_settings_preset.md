# ChatSettingsPreset

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / ChatSettingsPreset

> Auto-generated documentation for [julep.api.types.chat_settings_preset](../../../../../../../julep/api/types/chat_settings_preset.py) module.

- [ChatSettingsPreset](#chatsettingspreset)
  - [ChatSettingsPreset](#chatsettingspreset-1)

## ChatSettingsPreset

[Show source in chat_settings_preset.py:9](../../../../../../../julep/api/types/chat_settings_preset.py#L9)

Generation preset name (problem_solving|conversational|fun|prose|creative|business|deterministic|code|multilingual)

#### Signature

```python
class ChatSettingsPreset(str, enum.Enum): ...
```

### ChatSettingsPreset().visit

[Show source in chat_settings_preset.py:24](../../../../../../../julep/api/types/chat_settings_preset.py#L24)

#### Signature

```python
def visit(
    self,
    problem_solving: typing.Callable[[], T_Result],
    conversational: typing.Callable[[], T_Result],
    fun: typing.Callable[[], T_Result],
    prose: typing.Callable[[], T_Result],
    creative: typing.Callable[[], T_Result],
    business: typing.Callable[[], T_Result],
    deterministic: typing.Callable[[], T_Result],
    code: typing.Callable[[], T_Result],
    multilingual: typing.Callable[[], T_Result],
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)