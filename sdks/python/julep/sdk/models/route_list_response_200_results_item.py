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

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.transition import Transition


T = TypeVar("T", bound="RouteListResponse200ResultsItem")


@_attrs_define
class RouteListResponse200ResultsItem:
    """
    Attributes:
        transitions (List['Transition']):
    """

    transitions: List["Transition"]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.transition import Transition

        transitions = []
        for transitions_item_data in self.transitions:
            transitions_item = transitions_item_data.to_dict()
            transitions.append(transitions_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "transitions": transitions,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.transition import Transition

        d = src_dict.copy()
        transitions = []
        _transitions = d.pop("transitions")
        for transitions_item_data in _transitions:
            transitions_item = Transition.from_dict(transitions_item_data)

            transitions.append(transitions_item)

        route_list_response_200_results_item = cls(
            transitions=transitions,
        )

        route_list_response_200_results_item.additional_properties = d
        return route_list_response_200_results_item

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
