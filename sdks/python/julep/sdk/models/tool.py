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

from ..models.tool_type import ToolType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.function_def import FunctionDef


T = TypeVar("T", bound="Tool")


@_attrs_define
class Tool:
    """
    Attributes:
        type (ToolType):  Default: ToolType.FUNCTION.
        name (str): Valid python identifier names
        function (FunctionDef): Function definition
        created_at (datetime.datetime): When this resource was created as UTC date-time
        updated_at (datetime.datetime): When this resource was updated as UTC date-time
        id (str):
        integration (Union[Unset, Any]):
        system (Union[Unset, Any]):
        api_call (Union[Unset, Any]):
    """

    name: str
    function: "FunctionDef"
    created_at: datetime.datetime
    updated_at: datetime.datetime
    id: str
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

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        id = self.id

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
                "created_at": created_at,
                "updated_at": updated_at,
                "id": id,
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

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        id = d.pop("id")

        integration = d.pop("integration", UNSET)

        system = d.pop("system", UNSET)

        api_call = d.pop("api_call", UNSET)

        tool = cls(
            type=type,
            name=name,
            function=function,
            created_at=created_at,
            updated_at=updated_at,
            id=id,
            integration=integration,
            system=system,
            api_call=api_call,
        )

        tool.additional_properties = d
        return tool

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
