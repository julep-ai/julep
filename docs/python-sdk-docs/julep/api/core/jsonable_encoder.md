# Jsonable Encoder

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Core](./index.md#core) / Jsonable Encoder

> Auto-generated documentation for [julep.api.core.jsonable_encoder](../../../../../../../julep/api/core/jsonable_encoder.py) module.

- [Jsonable Encoder](#jsonable-encoder)
  - [generate_encoders_by_class_tuples](#generate_encoders_by_class_tuples)
  - [jsonable_encoder](#jsonable_encoder)

## generate_encoders_by_class_tuples

[Show source in jsonable_encoder.py:30](../../../../../../../julep/api/core/jsonable_encoder.py#L30)

#### Signature

```python
def generate_encoders_by_class_tuples(
    type_encoder_map: Dict[Any, Callable[[Any], Any]],
) -> Dict[Callable[[Any], Any], Tuple[Any, ...]]: ...
```



## jsonable_encoder

[Show source in jsonable_encoder.py:46](../../../../../../../julep/api/core/jsonable_encoder.py#L46)

#### Signature

```python
def jsonable_encoder(
    obj: Any, custom_encoder: Optional[Dict[Any, Callable[[Any], Any]]] = None
) -> Any: ...
```