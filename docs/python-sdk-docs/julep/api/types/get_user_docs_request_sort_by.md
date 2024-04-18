# GetUserDocsRequestSortBy

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / GetUserDocsRequestSortBy

> Auto-generated documentation for [julep.api.types.get_user_docs_request_sort_by](../../../../../../../julep/api/types/get_user_docs_request_sort_by.py) module.

- [GetUserDocsRequestSortBy](#getuserdocsrequestsortby)
  - [GetUserDocsRequestSortBy](#getuserdocsrequestsortby-1)

## GetUserDocsRequestSortBy

[Show source in get_user_docs_request_sort_by.py:9](../../../../../../../julep/api/types/get_user_docs_request_sort_by.py#L9)

#### Signature

```python
class GetUserDocsRequestSortBy(str, enum.Enum): ...
```

### GetUserDocsRequestSortBy().visit

[Show source in get_user_docs_request_sort_by.py:13](../../../../../../../julep/api/types/get_user_docs_request_sort_by.py#L13)

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