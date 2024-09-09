# Datetime Utils

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Julep Python Library](../index.md#julep-python-library) / [Core](./index.md#core) / Datetime Utils

> Auto-generated documentation for [julep.api.core.datetime_utils](../../../../../../../julep/api/core/datetime_utils.py) module.

- [Datetime Utils](#datetime-utils)
  - [serialize_datetime](#serialize_datetime)

## serialize_datetime

[Show source in datetime_utils.py:6](../../../../../../../julep/api/core/datetime_utils.py#L6)

Serialize a datetime including timezone info.

Uses the timezone info provided if present, otherwise uses the current runtime's timezone info.

UTC datetimes end in "Z" while all other timezones are represented as offset from UTC, e.g. +05:00.

#### Signature

```python
def serialize_datetime(v: dt.datetime) -> str: ...
```