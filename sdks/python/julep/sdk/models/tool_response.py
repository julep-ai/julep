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

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tool_response_output import ToolResponseOutput


T = TypeVar("T", bound="ToolResponse")


@_attrs_define
class ToolResponse:
    """
    Attributes:
        id (str):
        output (ToolResponseOutput): The output of the tool
    """

    id: str
    output: "ToolResponseOutput"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.tool_response_output import ToolResponseOutput

        id = self.id

        output = self.output.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "output": output,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.tool_response_output import ToolResponseOutput

        d = src_dict.copy()
        id = d.pop("id")

        output = ToolResponseOutput.from_dict(d.pop("output"))

        tool_response = cls(
            id=id,
            output=output,
        )

        tool_response.additional_properties = d
        return tool_response

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
