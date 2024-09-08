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

from ..models.job_state import JobState
from ..types import UNSET, Unset

T = TypeVar("T", bound="JobStatus")


@_attrs_define
class JobStatus:
    """
    Attributes:
        id (str):
        created_at (datetime.datetime): When this resource was created as UTC date-time
        updated_at (datetime.datetime): When this resource was updated as UTC date-time
        name (str): For Unicode character safety
            See: https://unicode.org/reports/tr31/
            See: https://www.unicode.org/reports/tr39/#Identifier_Characters Default: ''.
        reason (str): Reason for the current state of the job Default: ''.
        has_progress (bool): Whether this Job supports progress updates Default: False.
        progress (float): Progress percentage Default: 0.0.
        state (JobState): Current state (one of: pending, in_progress, retrying, succeeded, aborted, failed) Default:
            JobState.PENDING.
    """

    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    name: str = ""
    reason: str = ""
    has_progress: bool = False
    progress: float = 0.0
    state: JobState = JobState.PENDING
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        name = self.name

        reason = self.reason

        has_progress = self.has_progress

        progress = self.progress

        state = self.state.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "created_at": created_at,
                "updated_at": updated_at,
                "name": name,
                "reason": reason,
                "has_progress": has_progress,
                "progress": progress,
                "state": state,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        name = d.pop("name")

        reason = d.pop("reason")

        has_progress = d.pop("has_progress")

        progress = d.pop("progress")

        state = JobState(d.pop("state"))

        job_status = cls(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            name=name,
            reason=reason,
            has_progress=has_progress,
            progress=progress,
            state=state,
        )

        job_status.additional_properties = d
        return job_status

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
