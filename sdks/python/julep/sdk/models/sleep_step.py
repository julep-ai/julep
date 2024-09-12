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

from ..models.sleep_step_kind import SleepStepKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sleep_for import SleepFor


T = TypeVar("T", bound="SleepStep")


@_attrs_define
class SleepStep:
    """
    Attributes:
        kind (SleepStepKind): The kind of step Default: SleepStepKind.SLEEP.
        sleep (SleepFor):
    """

    sleep: "SleepFor"
    kind: SleepStepKind = SleepStepKind.SLEEP
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.sleep_for import SleepFor

        kind = self.kind.value

        sleep = self.sleep.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "sleep": sleep,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.sleep_for import SleepFor

        d = src_dict.copy()
        kind = SleepStepKind(d.pop("kind_"))

        sleep = SleepFor.from_dict(d.pop("sleep"))

        sleep_step = cls(
            kind=kind,
            sleep=sleep,
        )

        sleep_step.additional_properties = d
        return sleep_step

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
