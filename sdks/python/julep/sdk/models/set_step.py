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

from ..models.set_step_kind import SetStepKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.set_step_set import SetStepSet


T = TypeVar("T", bound="SetStep")


@_attrs_define
class SetStep:
    """
    Attributes:
        kind (SetStepKind): The kind of step
        set_ (SetStepSet): The value to set
    """

    kind: SetStepKind
    set_: "SetStepSet"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.set_step_set import SetStepSet

        kind = self.kind.value

        set_ = self.set_.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "set": set_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.set_step_set import SetStepSet

        d = src_dict.copy()
        kind = SetStepKind(d.pop("kind_"))

        set_ = SetStepSet.from_dict(d.pop("set"))

        set_step = cls(
            kind=kind,
            set_=set_,
        )

        set_step.additional_properties = d
        return set_step

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
