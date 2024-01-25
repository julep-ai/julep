# SuggestionTarget

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / SuggestionTarget

> Auto-generated documentation for [julep.api.types.suggestion_target](../../../../../../../julep/api/types/suggestion_target.py) module.

- [SuggestionTarget](#suggestiontarget)
  - [SuggestionTarget](#suggestiontarget-1)

## SuggestionTarget

[Show source in suggestion_target.py:9](../../../../../../../julep/api/types/suggestion_target.py#L9)

Whether the suggestion is for the `agent` or a `user`

#### Signature

```python
class SuggestionTarget(str, enum.Enum): ...
```

### SuggestionTarget().visit

[Show source in suggestion_target.py:17](../../../../../../../julep/api/types/suggestion_target.py#L17)

#### Signature

```python
def visit(
    self, user: typing.Callable[[], T_Result], agent: typing.Callable[[], T_Result]
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)