# ListSessionsRequestSortBy

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / ListSessionsRequestSortBy

> Auto-generated documentation for [julep.api.types.list_sessions_request_sort_by](../../../../../../../julep/api/types/list_sessions_request_sort_by.py) module.

- [ListSessionsRequestSortBy](#listsessionsrequestsortby)
  - [ListSessionsRequestSortBy](#listsessionsrequestsortby-1)

## ListSessionsRequestSortBy

[Show source in list_sessions_request_sort_by.py:9](../../../../../../../julep/api/types/list_sessions_request_sort_by.py#L9)

#### Signature

```python
class ListSessionsRequestSortBy(str, enum.Enum): ...
```

### ListSessionsRequestSortBy().visit

[Show source in list_sessions_request_sort_by.py:13](../../../../../../../julep/api/types/list_sessions_request_sort_by.py#L13)

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