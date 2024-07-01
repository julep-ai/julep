# ChatMlImageContentPartImageUrlDetail

[Julep Python SDK Index](../../../README.md#julep-python-sdk-index) / [Julep](../../index.md#julep) / [Api](../index.md#api) / [Types](./index.md#types) / ChatMlImageContentPartImageUrlDetail

> Auto-generated documentation for [julep.api.types.chat_ml_image_content_part_image_url_detail](../../../../../../../julep/api/types/chat_ml_image_content_part_image_url_detail.py) module.

- [ChatMlImageContentPartImageUrlDetail](#chatmlimagecontentpartimageurldetail)
  - [ChatMlImageContentPartImageUrlDetail](#chatmlimagecontentpartimageurldetail-1)

## ChatMlImageContentPartImageUrlDetail

[Show source in chat_ml_image_content_part_image_url_detail.py:9](../../../../../../../julep/api/types/chat_ml_image_content_part_image_url_detail.py#L9)

image detail to feed into the model can be low | high | auto

#### Signature

```python
class ChatMlImageContentPartImageUrlDetail(str, enum.Enum): ...
```

### ChatMlImageContentPartImageUrlDetail().visit

[Show source in chat_ml_image_content_part_image_url_detail.py:18](../../../../../../../julep/api/types/chat_ml_image_content_part_image_url_detail.py#L18)

#### Signature

```python
def visit(
    self,
    low: typing.Callable[[], T_Result],
    high: typing.Callable[[], T_Result],
    auto: typing.Callable[[], T_Result],
) -> T_Result: ...
```

#### See also

- [T_Result](#t_result)