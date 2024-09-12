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

from ..models.switch_step_kind import SwitchStepKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.case_then import CaseThen


T = TypeVar("T", bound="SwitchStep")


@_attrs_define
class SwitchStep:
    """
    Attributes:
        kind (SwitchStepKind): The kind of step Default: SwitchStepKind.SWITCH.
        switch (List['CaseThen']): The cond tree
    """

    switch: List["CaseThen"]
    kind: SwitchStepKind = SwitchStepKind.SWITCH
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.case_then import CaseThen

        kind = self.kind.value

        switch = []
        for switch_item_data in self.switch:
            switch_item = switch_item_data.to_dict()
            switch.append(switch_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "switch": switch,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.case_then import CaseThen

        d = src_dict.copy()
        kind = SwitchStepKind(d.pop("kind_"))

        switch = []
        _switch = d.pop("switch")
        for switch_item_data in _switch:
            switch_item = CaseThen.from_dict(switch_item_data)

            switch.append(switch_item)

        switch_step = cls(
            kind=kind,
            switch=switch,
        )

        switch_step.additional_properties = d
        return switch_step

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
