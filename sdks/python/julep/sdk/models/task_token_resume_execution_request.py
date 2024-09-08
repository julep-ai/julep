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

from ..models.task_token_resume_execution_request_status import (
    TaskTokenResumeExecutionRequestStatus,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.task_token_resume_execution_request_input import (
        TaskTokenResumeExecutionRequestInput,
    )


T = TypeVar("T", bound="TaskTokenResumeExecutionRequest")


@_attrs_define
class TaskTokenResumeExecutionRequest:
    """
    Attributes:
        status (TaskTokenResumeExecutionRequestStatus):  Default: TaskTokenResumeExecutionRequestStatus.RUNNING.
        input_ (Union[Unset, TaskTokenResumeExecutionRequestInput]): The input to resume the execution with
    """

    status: TaskTokenResumeExecutionRequestStatus = (
        TaskTokenResumeExecutionRequestStatus.RUNNING
    )
    input_: Union[Unset, "TaskTokenResumeExecutionRequestInput"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.task_token_resume_execution_request_input import (
            TaskTokenResumeExecutionRequestInput,
        )

        status = self.status.value

        input_: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.input_, Unset):
            input_ = self.input_.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
            }
        )
        if input_ is not UNSET:
            field_dict["input"] = input_

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.task_token_resume_execution_request_input import (
            TaskTokenResumeExecutionRequestInput,
        )

        d = src_dict.copy()
        status = TaskTokenResumeExecutionRequestStatus(d.pop("status"))

        _input_ = d.pop("input", UNSET)
        input_: Union[Unset, TaskTokenResumeExecutionRequestInput]
        if isinstance(_input_, Unset):
            input_ = UNSET
        else:
            input_ = TaskTokenResumeExecutionRequestInput.from_dict(_input_)

        task_token_resume_execution_request = cls(
            status=status,
            input_=input_,
        )

        task_token_resume_execution_request.additional_properties = d
        return task_token_resume_execution_request

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
