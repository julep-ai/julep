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

from ..models.chosen_system_call_type import ChosenSystemCallType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ChosenSystemCall")


@_attrs_define
class ChosenSystemCall:
    """
    Attributes:
        type (ChosenSystemCallType):
        system (Any):
        id (str):
    """

    type: ChosenSystemCallType
    system: Any
    id: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        system = self.system

        id = self.id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type,
                "system": system,
                "id": id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = ChosenSystemCallType(d.pop("type"))

        system = d.pop("system")

        id = d.pop("id")

        chosen_system_call = cls(
            type=type,
            system=system,
            id=id,
        )

        chosen_system_call.additional_properties = d
        return chosen_system_call

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
