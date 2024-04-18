# ListAgentsRequestSortBy

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / ListAgentsRequestSortBy

> Auto-generated documentation for [julep.api.types.list_agents_request_sort_by](../../../../../../../julep/api/types/list_agents_request_sort_by.py) module.

- [ListAgentsRequestSortBy](#listagentsrequestsortby)
  - [ListAgentsRequestSortBy](#listagentsrequestsortby-1)

## ListAgentsRequestSortBy

[Show source in list_agents_request_sort_by.py:9](../../../../../../../julep/api/types/list_agents_request_sort_by.py#L9)

#### Signature

```python
class ListAgentsRequestSortBy(str, enum.Enum): ...
```

### ListAgentsRequestSortBy().visit

[Show source in list_agents_request_sort_by.py:13](../../../../../../../julep/api/types/list_agents_request_sort_by.py#L13)

#### Signature

```python
def visit(
    self,
    created_at: typing.Callable[[], T_Result],
    updated_at: typing.Callable[[], T_Result],
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)