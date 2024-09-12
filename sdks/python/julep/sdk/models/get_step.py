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

from ..models.get_step_kind import GetStepKind
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetStep")


@_attrs_define
class GetStep:
    """
    Attributes:
        kind (GetStepKind): The kind of step Default: GetStepKind.GET.
        get (str): The key to get
    """

    get: str
    kind: GetStepKind = GetStepKind.GET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        kind = self.kind.value

        get = self.get

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "get": get,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        kind = GetStepKind(d.pop("kind_"))

        get = d.pop("get")

        get_step = cls(
            kind=kind,
            get=get,
        )

        get_step.additional_properties = d
        return get_step

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
