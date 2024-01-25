# ToolType

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / ToolType

> Auto-generated documentation for [julep.api.types.tool_type](../../../../../../../julep/api/types/tool_type.py) module.

- [ToolType](#tooltype)
  - [ToolType](#tooltype-1)

## ToolType

[Show source in tool_type.py:9](../../../../../../../julep/api/types/tool_type.py#L9)

Whether this tool is a `function` or a `webhook` (Only `function` tool supported right now)

#### Signature

```python
class ToolType(str, enum.Enum): ...
```

### ToolType().visit

[Show source in tool_type.py:17](../../../../../../../julep/api/types/tool_type.py#L17)

#### Signature

```python
def visit(
    self, function: typing.Callable[[], T_Result], webhook: typing.Callable[[], T_Result]
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)