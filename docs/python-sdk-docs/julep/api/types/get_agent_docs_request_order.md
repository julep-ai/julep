# GetAgentDocsRequestOrder

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / GetAgentDocsRequestOrder

> Auto-generated documentation for [julep.api.types.get_agent_docs_request_order](../../../../../../../julep/api/types/get_agent_docs_request_order.py) module.

- [GetAgentDocsRequestOrder](#getagentdocsrequestorder)
  - [GetAgentDocsRequestOrder](#getagentdocsrequestorder-1)

## GetAgentDocsRequestOrder

[Show source in get_agent_docs_request_order.py:9](../../../../../../../julep/api/types/get_agent_docs_request_order.py#L9)

#### Signature

```python
class GetAgentDocsRequestOrder(str, enum.Enum): ...
```

### GetAgentDocsRequestOrder().visit

[Show source in get_agent_docs_request_order.py:13](../../../../../../../julep/api/types/get_agent_docs_request_order.py#L13)

#### Signature

```python
def visit(
    self, asc: typing.Callable[[], T_Result], desc: typing.Callable[[], T_Result]
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)