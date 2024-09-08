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

from ..models.chosen_api_call_type import ChosenApiCallType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ChosenApiCall")


@_attrs_define
class ChosenApiCall:
    """
    Attributes:
        type (ChosenApiCallType):
        api_call (Any):
        id (str):
    """

    type: ChosenApiCallType
    api_call: Any
    id: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        api_call = self.api_call

        id = self.id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type,
                "api_call": api_call,
                "id": id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = ChosenApiCallType(d.pop("type"))

        api_call = d.pop("api_call")

        id = d.pop("id")

        chosen_api_call = cls(
            type=type,
            api_call=api_call,
            id=id,
        )

        chosen_api_call.additional_properties = d
        return chosen_api_call

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
