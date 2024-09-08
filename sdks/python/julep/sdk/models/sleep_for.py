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

from ..types import UNSET, Unset

T = TypeVar("T", bound="SleepFor")


@_attrs_define
class SleepFor:
    """
    Attributes:
        seconds (int): The number of seconds to sleep for Default: 0.
        minutes (int): The number of minutes to sleep for Default: 0.
        hours (int): The number of hours to sleep for Default: 0.
        days (int): The number of days to sleep for Default: 0.
    """

    seconds: int = 0
    minutes: int = 0
    hours: int = 0
    days: int = 0
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        seconds = self.seconds

        minutes = self.minutes

        hours = self.hours

        days = self.days

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "seconds": seconds,
                "minutes": minutes,
                "hours": hours,
                "days": days,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        seconds = d.pop("seconds")

        minutes = d.pop("minutes")

        hours = d.pop("hours")

        days = d.pop("days")

        sleep_for = cls(
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days,
        )

        sleep_for.additional_properties = d
        return sleep_for

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
