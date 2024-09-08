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

from ..models.wait_for_input_step_kind import WaitForInputStepKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.wait_for_input_info import WaitForInputInfo


T = TypeVar("T", bound="WaitForInputStep")


@_attrs_define
class WaitForInputStep:
    """
    Attributes:
        kind (WaitForInputStepKind): The kind of step
        wait_for_input (WaitForInputInfo):
    """

    kind: WaitForInputStepKind
    wait_for_input: "WaitForInputInfo"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.wait_for_input_info import WaitForInputInfo

        kind = self.kind.value

        wait_for_input = self.wait_for_input.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "wait_for_input": wait_for_input,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.wait_for_input_info import WaitForInputInfo

        d = src_dict.copy()
        kind = WaitForInputStepKind(d.pop("kind_"))

        wait_for_input = WaitForInputInfo.from_dict(d.pop("wait_for_input"))

        wait_for_input_step = cls(
            kind=kind,
            wait_for_input=wait_for_input,
        )

        wait_for_input_step.additional_properties = d
        return wait_for_input_step

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
