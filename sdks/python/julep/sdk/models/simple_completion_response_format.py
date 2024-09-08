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
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.simple_completion_response_format_type import (
    SimpleCompletionResponseFormatType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="SimpleCompletionResponseFormat")


@_attrs_define
class SimpleCompletionResponseFormat:
    """
    Attributes:
        type (SimpleCompletionResponseFormatType): The format of the response Default:
            SimpleCompletionResponseFormatType.TEXT.
    """

    type: SimpleCompletionResponseFormatType = SimpleCompletionResponseFormatType.TEXT
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = SimpleCompletionResponseFormatType(d.pop("type"))

        simple_completion_response_format = cls(
            type=type,
        )

        simple_completion_response_format.additional_properties = d
        return simple_completion_response_format

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
