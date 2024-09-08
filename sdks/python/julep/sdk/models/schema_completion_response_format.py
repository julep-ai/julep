from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Dict,
    List,
    Optional,
    TextIO,
    Tuple,
    Type,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.schema_completion_response_format_type import (
    SchemaCompletionResponseFormatType,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.schema_completion_response_format_json_schema import (
        SchemaCompletionResponseFormatJsonSchema,
    )


T = TypeVar("T", bound="SchemaCompletionResponseFormat")


@_attrs_define
class SchemaCompletionResponseFormat:
    """
    Attributes:
        type (SchemaCompletionResponseFormatType): The format of the response Default:
            SchemaCompletionResponseFormatType.JSON_SCHEMA.
        json_schema (SchemaCompletionResponseFormatJsonSchema): The schema of the response
    """

    json_schema: "SchemaCompletionResponseFormatJsonSchema"
    type: SchemaCompletionResponseFormatType = (
        SchemaCompletionResponseFormatType.JSON_SCHEMA
    )
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.schema_completion_response_format_json_schema import (
            SchemaCompletionResponseFormatJsonSchema,
        )

        type = self.type.value

        json_schema = self.json_schema.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type,
                "json_schema": json_schema,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.schema_completion_response_format_json_schema import (
            SchemaCompletionResponseFormatJsonSchema,
        )

        d = src_dict.copy()
        type = SchemaCompletionResponseFormatType(d.pop("type"))

        json_schema = SchemaCompletionResponseFormatJsonSchema.from_dict(
            d.pop("json_schema")
        )

        schema_completion_response_format = cls(
            type=type,
            json_schema=json_schema,
        )

        schema_completion_response_format.additional_properties = d
        return schema_completion_response_format

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
