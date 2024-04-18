# ListUsersRequestOrder

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / ListUsersRequestOrder

> Auto-generated documentation for [julep.api.types.list_users_request_order](../../../../../../../julep/api/types/list_users_request_order.py) module.

- [ListUsersRequestOrder](#listusersrequestorder)
  - [ListUsersRequestOrder](#listusersrequestorder-1)

## ListUsersRequestOrder

[Show source in list_users_request_order.py:9](../../../../../../../julep/api/types/list_users_request_order.py#L9)

#### Signature

```python
class ListUsersRequestOrder(str, enum.Enum): ...
```

### ListUsersRequestOrder().visit

[Show source in list_users_request_order.py:13](../../../../../../../julep/api/types/list_users_request_order.py#L13)

#### Signature

```python
def visit(
    self, asc: typing.Callable[[], T_Result], desc: typing.Callable[[], T_Result]
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)