# ChatResponseFinishReason

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / ChatResponseFinishReason

> Auto-generated documentation for [julep.api.types.chat_response_finish_reason](../../../../../../../julep/api/types/chat_response_finish_reason.py) module.

- [ChatResponseFinishReason](#chatresponsefinishreason)
  - [ChatResponseFinishReason](#chatresponsefinishreason-1)

## ChatResponseFinishReason

[Show source in chat_response_finish_reason.py:9](../../../../../../../julep/api/types/chat_response_finish_reason.py#L9)

The reason the model stopped generating tokens. This will be `stop` if the model hit a natural stop point or a provided stop sequence, `length` if the maximum number of tokens specified in the request was reached, `content_filter` if content was omitted due to a flag from our content filters, `tool_calls` if the model called a tool, or `function_call` (deprecated) if the model called a function.

#### Signature

```python
class ChatResponseFinishReason(str, enum.Enum): ...
```

### ChatResponseFinishReason().visit

[Show source in chat_response_finish_reason.py:20](../../../../../../../julep/api/types/chat_response_finish_reason.py#L20)

#### Signature

```python
def visit(
    self,
    stop: typing.Callable[[], T_Result],
    length: typing.Callable[[], T_Result],
    tool_calls: typing.Callable[[], T_Result],
    content_filter: typing.Callable[[], T_Result],
    function_call: typing.Callable[[], T_Result],
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)