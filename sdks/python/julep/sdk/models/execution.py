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

from ..models.execution_status import ExecutionStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.execution_input import ExecutionInput
    from ..models.execution_metadata import ExecutionMetadata


T = TypeVar("T", bound="Execution")


@_attrs_define
class Execution:
    """
    Attributes:
        task_id (str):
        status (ExecutionStatus): The status of the execution
        input_ (ExecutionInput): The input to the execution
        created_at (datetime.datetime): When this resource was created as UTC date-time
        updated_at (datetime.datetime): When this resource was updated as UTC date-time
        id (str):
        output (Union[Unset, Any]): The output of the execution if it succeeded
        error (Union[Unset, str]): The error of the execution if it failed
        metadata (Union[Unset, ExecutionMetadata]):
    """

    task_id: str
    status: ExecutionStatus
    input_: "ExecutionInput"
    created_at: datetime.datetime
    updated_at: datetime.datetime
    id: str
    output: Union[Unset, Any] = UNSET
    error: Union[Unset, str] = UNSET
    metadata: Union[Unset, "ExecutionMetadata"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.execution_input import ExecutionInput
        from ..models.execution_metadata import ExecutionMetadata

        task_id = self.task_id

        status = self.status.value

        input_ = self.input_.to_dict()

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        id = self.id

        output = self.output

        error = self.error

        metadata: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "task_id": task_id,
                "status": status,
                "input": input_,
                "created_at": created_at,
                "updated_at": updated_at,
                "id": id,
            }
        )
        if output is not UNSET:
            field_dict["output"] = output
        if error is not UNSET:
            field_dict["error"] = error
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.execution_input import ExecutionInput
        from ..models.execution_metadata import ExecutionMetadata

        d = src_dict.copy()
        task_id = d.pop("task_id")

        status = ExecutionStatus(d.pop("status"))

        input_ = ExecutionInput.from_dict(d.pop("input"))

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        id = d.pop("id")

        output = d.pop("output", UNSET)

        error = d.pop("error", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, ExecutionMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = ExecutionMetadata.from_dict(_metadata)

        execution = cls(
            task_id=task_id,
            status=status,
            input_=input_,
            created_at=created_at,
            updated_at=updated_at,
            id=id,
            output=output,
            error=error,
            metadata=metadata,
        )

        execution.additional_properties = d
        return execution

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
