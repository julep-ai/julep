# ListSessionsRequestOrder

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / ListSessionsRequestOrder

> Auto-generated documentation for [julep.api.types.list_sessions_request_order](../../../../../../../julep/api/types/list_sessions_request_order.py) module.

- [ListSessionsRequestOrder](#listsessionsrequestorder)
  - [ListSessionsRequestOrder](#listsessionsrequestorder-1)

## ListSessionsRequestOrder

[Show source in list_sessions_request_order.py:9](../../../../../../../julep/api/types/list_sessions_request_order.py#L9)

#### Signature

```python
class ListSessionsRequestOrder(str, enum.Enum): ...
```

### ListSessionsRequestOrder().visit

[Show source in list_sessions_request_order.py:13](../../../../../../../julep/api/types/list_sessions_request_order.py#L13)

#### Signature

```python
def visit(
    self, asc: typing.Callable[[], T_Result], desc: typing.Callable[[], T_Result]
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)