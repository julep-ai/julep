# File

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Julep Python Library](../index.md#julep-python-library) / [Core](./index.md#core) / File

> Auto-generated documentation for [julep.api.core.file](../../../../../../../julep/api/core/file.py) module.

#### Attributes

- `FileContent` - File typing inspired by the flexibility of types within the httpx library
  https://github.com/encode/httpx/blob/master/httpx/_types.py: typing.Union[typing.IO[bytes], bytes, str]


- [File](#file)
  - [convert_file_dict_to_httpx_tuples](#convert_file_dict_to_httpx_tuples)

## convert_file_dict_to_httpx_tuples

[Show source in file.py:25](../../../../../../../julep/api/core/file.py#L25)

The format we use is a list of tuples, where the first element is the
name of the file and the second is the file object. Typically HTTPX wants
a dict, but to be able to send lists of files, you have to use the list
approach (which also works for non-lists)
https://github.com/encode/httpx/pull/1032

#### Signature

```python
def convert_file_dict_to_httpx_tuples(
    d: typing.Dict[str, typing.Union[File, typing.List[File]]],
) -> typing.List[typing.Tuple[str, File]]: ...
```

#### See also

- [File](#file)