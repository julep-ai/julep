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

from ..models.error_workflow_step_kind import ErrorWorkflowStepKind
from ..types import UNSET, Unset

T = TypeVar("T", bound="ErrorWorkflowStep")


@_attrs_define
class ErrorWorkflowStep:
    """
    Attributes:
        kind (ErrorWorkflowStepKind): The kind of step Default: ErrorWorkflowStepKind.ERROR.
        error (str): The error message
    """

    error: str
    kind: ErrorWorkflowStepKind = ErrorWorkflowStepKind.ERROR
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        kind = self.kind.value

        error = self.error

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "error": error,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        kind = ErrorWorkflowStepKind(d.pop("kind_"))

        error = d.pop("error")

        error_workflow_step = cls(
            kind=kind,
            error=error,
        )

        error_workflow_step.additional_properties = d
        return error_workflow_step

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
