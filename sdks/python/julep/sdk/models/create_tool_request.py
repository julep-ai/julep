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

from ..models.tool_type import ToolType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.function_def import FunctionDef


T = TypeVar("T", bound="CreateToolRequest")


@_attrs_define
class CreateToolRequest:
    """Payload for creating a tool

    Attributes:
        type (ToolType):  Default: ToolType.FUNCTION.
        name (str): Valid python identifier names
        function (FunctionDef): Function definition
        integration (Union[Unset, Any]):
        system (Union[Unset, Any]):
        api_call (Union[Unset, Any]):
    """

    name: str
    function: "FunctionDef"
    type: ToolType = ToolType.FUNCTION
    integration: Union[Unset, Any] = UNSET
    system: Union[Unset, Any] = UNSET
    api_call: Union[Unset, Any] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.function_def import FunctionDef

        type = self.type.value

        name = self.name

        function = self.function.to_dict()

        integration = self.integration

        system = self.system

        api_call = self.api_call

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type,
                "name": name,
                "function": function,
            }
        )
        if integration is not UNSET:
            field_dict["integration"] = integration
        if system is not UNSET:
            field_dict["system"] = system
        if api_call is not UNSET:
            field_dict["api_call"] = api_call

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.function_def import FunctionDef

        d = src_dict.copy()
        type = ToolType(d.pop("type"))

        name = d.pop("name")

        function = FunctionDef.from_dict(d.pop("function"))

        integration = d.pop("integration", UNSET)

        system = d.pop("system", UNSET)

        api_call = d.pop("api_call", UNSET)

        create_tool_request = cls(
            type=type,
            name=name,
            function=function,
            integration=integration,
            system=system,
            api_call=api_call,
        )

        create_tool_request.additional_properties = d
        return create_tool_request

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
