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

from ..models.foreach_step_kind import ForeachStepKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.foreach_do import ForeachDo


T = TypeVar("T", bound="ForeachStep")


@_attrs_define
class ForeachStep:
    """
    Attributes:
        kind (ForeachStepKind): The kind of step
        foreach (ForeachDo):
    """

    kind: ForeachStepKind
    foreach: "ForeachDo"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.foreach_do import ForeachDo

        kind = self.kind.value

        foreach = self.foreach.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "foreach": foreach,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.foreach_do import ForeachDo

        d = src_dict.copy()
        kind = ForeachStepKind(d.pop("kind_"))

        foreach = ForeachDo.from_dict(d.pop("foreach"))

        foreach_step = cls(
            kind=kind,
            foreach=foreach,
        )

        foreach_step.additional_properties = d
        return foreach_step

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
