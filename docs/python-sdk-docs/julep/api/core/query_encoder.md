# Query Encoder

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Julep Python Library](../index.md#julep-python-library) / [Core](./index.md#core) / Query Encoder

> Auto-generated documentation for [julep.api.core.query_encoder](../../../../../../../julep/api/core/query_encoder.py) module.

- [Query Encoder](#query-encoder)
  - [encode_query](#encode_query)
  - [single_query_encoder](#single_query_encoder)
  - [traverse_query_dict](#traverse_query_dict)

## encode_query

[Show source in query_encoder.py:34](../../../../../../../julep/api/core/query_encoder.py#L34)

#### Signature

```python
def encode_query(query: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]: ...
```



## single_query_encoder

[Show source in query_encoder.py:23](../../../../../../../julep/api/core/query_encoder.py#L23)

#### Signature

```python
def single_query_encoder(query_key: str, query_value: Any) -> Dict[str, Any]: ...
```



## traverse_query_dict

[Show source in query_encoder.py:10](../../../../../../../julep/api/core/query_encoder.py#L10)

#### Signature

```python
def traverse_query_dict(
    dict_flat: Dict[str, Any], key_prefix: Optional[str] = None
) -> Dict[str, Any]: ...
```