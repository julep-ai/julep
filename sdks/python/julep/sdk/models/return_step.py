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

from ..models.return_step_kind import ReturnStepKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.return_step_return import ReturnStepReturn


T = TypeVar("T", bound="ReturnStep")


@_attrs_define
class ReturnStep:
    """
    Attributes:
        kind (ReturnStepKind): The kind of step Default: ReturnStepKind.RETURN.
        return_ (ReturnStepReturn): The value to return
    """

    return_: "ReturnStepReturn"
    kind: ReturnStepKind = ReturnStepKind.RETURN
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.return_step_return import ReturnStepReturn

        kind = self.kind.value

        return_ = self.return_.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "return": return_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.return_step_return import ReturnStepReturn

        d = src_dict.copy()
        kind = ReturnStepKind(d.pop("kind_"))

        return_ = ReturnStepReturn.from_dict(d.pop("return"))

        return_step = cls(
            kind=kind,
            return_=return_,
        )

        return_step.additional_properties = d
        return return_step

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
