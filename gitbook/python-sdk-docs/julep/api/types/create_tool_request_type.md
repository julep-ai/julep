# CreateToolRequestType

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / CreateToolRequestType

> Auto-generated documentation for [julep.api.types.create_tool_request_type](../../../../../../../julep/api/types/create_tool_request_type.py) module.

- [CreateToolRequestType](#createtoolrequesttype)
  - [CreateToolRequestType](#createtoolrequesttype-1)

## CreateToolRequestType

[Show source in create_tool_request_type.py:9](../../../../../../../julep/api/types/create_tool_request_type.py#L9)

Whether this tool is a `function` or a `webhook` (Only `function` tool supported right now)

#### Signature

```python
class CreateToolRequestType(str, enum.Enum): ...
```

### CreateToolRequestType().visit

[Show source in create_tool_request_type.py:17](../../../../../../../julep/api/types/create_tool_request_type.py#L17)

#### Signature

```python
def visit(
    self, function: typing.Callable[[], T_Result], webhook: typing.Callable[[], T_Result]
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)