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
    Union,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.transition_type import TransitionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.transition_metadata import TransitionMetadata
    from ..models.transition_target import TransitionTarget


T = TypeVar("T", bound="Transition")


@_attrs_define
class Transition:
    """
    Attributes:
        type (TransitionType):
        output (Any):
        created_at (datetime.datetime): When this resource was created as UTC date-time
        updated_at (datetime.datetime): When this resource was updated as UTC date-time
        execution_id (str):
        current (TransitionTarget):
        next_ (TransitionTarget):
        id (str):
        metadata (Union[Unset, TransitionMetadata]):
    """

    type: TransitionType
    output: Any
    created_at: datetime.datetime
    updated_at: datetime.datetime
    execution_id: str
    current: "TransitionTarget"
    next_: "TransitionTarget"
    id: str
    metadata: Union[Unset, "TransitionMetadata"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.transition_metadata import TransitionMetadata
        from ..models.transition_target import TransitionTarget

        type = self.type.value

        output = self.output

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        execution_id = self.execution_id

        current = self.current.to_dict()

        next_ = self.next_.to_dict()

        id = self.id

        metadata: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type,
                "output": output,
                "created_at": created_at,
                "updated_at": updated_at,
                "execution_id": execution_id,
                "current": current,
                "next": next_,
                "id": id,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.transition_metadata import TransitionMetadata
        from ..models.transition_target import TransitionTarget

        d = src_dict.copy()
        type = TransitionType(d.pop("type"))

        output = d.pop("output")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        execution_id = d.pop("execution_id")

        current = TransitionTarget.from_dict(d.pop("current"))

        next_ = TransitionTarget.from_dict(d.pop("next"))

        id = d.pop("id")

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, TransitionMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = TransitionMetadata.from_dict(_metadata)

        transition = cls(
            type=type,
            output=output,
            created_at=created_at,
            updated_at=updated_at,
            execution_id=execution_id,
            current=current,
            next_=next_,
            id=id,
            metadata=metadata,
        )

        transition.additional_properties = d
        return transition

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
