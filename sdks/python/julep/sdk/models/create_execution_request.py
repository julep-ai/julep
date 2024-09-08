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

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_execution_request_input import CreateExecutionRequestInput
    from ..models.create_execution_request_metadata import (
        CreateExecutionRequestMetadata,
    )


T = TypeVar("T", bound="CreateExecutionRequest")


@_attrs_define
class CreateExecutionRequest:
    """Payload for creating an execution

    Attributes:
        input_ (CreateExecutionRequestInput): The input to the execution
        output (Union[Unset, Any]): The output of the execution if it succeeded
        error (Union[Unset, str]): The error of the execution if it failed
        metadata (Union[Unset, CreateExecutionRequestMetadata]):
    """

    input_: "CreateExecutionRequestInput"
    output: Union[Unset, Any] = UNSET
    error: Union[Unset, str] = UNSET
    metadata: Union[Unset, "CreateExecutionRequestMetadata"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.create_execution_request_input import CreateExecutionRequestInput
        from ..models.create_execution_request_metadata import (
            CreateExecutionRequestMetadata,
        )

        input_ = self.input_.to_dict()

        output = self.output

        error = self.error

        metadata: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "input": input_,
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
        from ..models.create_execution_request_input import CreateExecutionRequestInput
        from ..models.create_execution_request_metadata import (
            CreateExecutionRequestMetadata,
        )

        d = src_dict.copy()
        input_ = CreateExecutionRequestInput.from_dict(d.pop("input"))

        output = d.pop("output", UNSET)

        error = d.pop("error", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, CreateExecutionRequestMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = CreateExecutionRequestMetadata.from_dict(_metadata)

        create_execution_request = cls(
            input_=input_,
            output=output,
            error=error,
            metadata=metadata,
        )

        create_execution_request.additional_properties = d
        return create_execution_request

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
