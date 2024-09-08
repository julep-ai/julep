import datetime
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
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ResourceUpdatedResponse")


@_attrs_define
class ResourceUpdatedResponse:
    """
    Attributes:
        id (str):
        updated_at (datetime.datetime): When this resource was updated as UTC date-time
        jobs (List[str]): IDs (if any) of jobs created as part of this request
    """

    id: str
    updated_at: datetime.datetime
    jobs: List[str]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        updated_at = self.updated_at.isoformat()

        jobs = self.jobs

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "updated_at": updated_at,
                "jobs": jobs,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        updated_at = isoparse(d.pop("updated_at"))

        jobs = cast(List[str], d.pop("jobs"))

        resource_updated_response = cls(
            id=id,
            updated_at=updated_at,
            jobs=jobs,
        )

        resource_updated_response.additional_properties = d
        return resource_updated_response

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
