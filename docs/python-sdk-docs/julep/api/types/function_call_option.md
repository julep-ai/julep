# FunctionCallOption

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / FunctionCallOption

> Auto-generated documentation for [julep.api.types.function_call_option](../../../../../../../julep/api/types/function_call_option.py) module.

- [FunctionCallOption](#functioncalloption)
  - [FunctionCallOption](#functioncalloption-1)

## FunctionCallOption

[Show source in function_call_option.py:14](../../../../../../../julep/api/types/function_call_option.py#L14)

Specifying a particular function via `{"name": "my_function"}` forces the model to call that function.

#### Signature

```python
class FunctionCallOption(pydantic.BaseModel): ...
```

### FunctionCallOption().dict

[Show source in function_call_option.py:29](../../../../../../../julep/api/types/function_call_option.py#L29)

#### Signature

```python
def dict(self, **kwargs: typing.Any) -> typing.Dict[str, typing.Any]: ...
```

### FunctionCallOption().json

[Show source in function_call_option.py:21](../../../../../../../julep/api/types/function_call_option.py#L21)

#### Signature

```python
def json(self, **kwargs: typing.Any) -> str: ...
```