# GetAgentDocsRequestSortBy

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / GetAgentDocsRequestSortBy

> Auto-generated documentation for [julep.api.types.get_agent_docs_request_sort_by](../../../../../../../julep/api/types/get_agent_docs_request_sort_by.py) module.

- [GetAgentDocsRequestSortBy](#getagentdocsrequestsortby)
  - [GetAgentDocsRequestSortBy](#getagentdocsrequestsortby-1)

## GetAgentDocsRequestSortBy

[Show source in get_agent_docs_request_sort_by.py:9](../../../../../../../julep/api/types/get_agent_docs_request_sort_by.py#L9)

#### Signature

```python
class GetAgentDocsRequestSortBy(str, enum.Enum): ...
```

### GetAgentDocsRequestSortBy().visit

[Show source in get_agent_docs_request_sort_by.py:13](../../../../../../../julep/api/types/get_agent_docs_request_sort_by.py#L13)

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