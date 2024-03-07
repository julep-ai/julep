# JobStatusState

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / JobStatusState

> Auto-generated documentation for [julep.api.types.job_status_state](../../../../../../../julep/api/types/job_status_state.py) module.

- [JobStatusState](#jobstatusstate)
  - [JobStatusState](#jobstatusstate-1)

## JobStatusState

[Show source in job_status_state.py:9](../../../../../../../julep/api/types/job_status_state.py#L9)

Current state (one of: pending, in_progress, retrying, succeeded, aborted, failed)

#### Signature

```python
class JobStatusState(str, enum.Enum): ...
```

### JobStatusState().visit

[Show source in job_status_state.py:22](../../../../../../../julep/api/types/job_status_state.py#L22)

#### Signature

```python
def visit(
    self,
    pending: typing.Callable[[], T_Result],
    in_progress: typing.Callable[[], T_Result],
    retrying: typing.Callable[[], T_Result],
    succeeded: typing.Callable[[], T_Result],
    aborted: typing.Callable[[], T_Result],
    failed: typing.Callable[[], T_Result],
    unknown: typing.Callable[[], T_Result],
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)