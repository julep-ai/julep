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

from ..models.chosen_integration_call_type import ChosenIntegrationCallType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ChosenIntegrationCall")


@_attrs_define
class ChosenIntegrationCall:
    """
    Attributes:
        type (ChosenIntegrationCallType):
        integration (Any):
        id (str):
    """

    type: ChosenIntegrationCallType
    integration: Any
    id: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        integration = self.integration

        id = self.id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type,
                "integration": integration,
                "id": id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = ChosenIntegrationCallType(d.pop("type"))

        integration = d.pop("integration")

        id = d.pop("id")

        chosen_integration_call = cls(
            type=type,
            integration=integration,
            id=id,
        )

        chosen_integration_call.additional_properties = d
        return chosen_integration_call

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
