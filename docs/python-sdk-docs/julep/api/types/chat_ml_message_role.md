# ChatMlMessageRole

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / ChatMlMessageRole

> Auto-generated documentation for [julep.api.types.chat_ml_message_role](../../../../../../../julep/api/types/chat_ml_message_role.py) module.

- [ChatMlMessageRole](#chatmlmessagerole)
  - [ChatMlMessageRole](#chatmlmessagerole-1)

## ChatMlMessageRole

[Show source in chat_ml_message_role.py:9](../../../../../../../julep/api/types/chat_ml_message_role.py#L9)

ChatML role (system|assistant|user|function_call)

#### Signature

```python
class ChatMlMessageRole(str, enum.Enum): ...
```

### ChatMlMessageRole().visit

[Show source in chat_ml_message_role.py:20](../../../../../../../julep/api/types/chat_ml_message_role.py#L20)

#### Signature

```python
def visit(
    self,
    user: typing.Callable[[], T_Result],
    assistant: typing.Callable[[], T_Result],
    system: typing.Callable[[], T_Result],
    function_call: typing.Callable[[], T_Result],
    function: typing.Callable[[], T_Result],
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)