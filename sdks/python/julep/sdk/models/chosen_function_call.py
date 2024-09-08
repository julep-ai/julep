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

from ..models.chosen_function_call_type import ChosenFunctionCallType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.function_call_option import FunctionCallOption


T = TypeVar("T", bound="ChosenFunctionCall")


@_attrs_define
class ChosenFunctionCall:
    """
    Attributes:
        type (ChosenFunctionCallType):
        function (FunctionCallOption):
        id (str):
    """

    type: ChosenFunctionCallType
    function: "FunctionCallOption"
    id: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.function_call_option import FunctionCallOption

        type = self.type.value

        function = self.function.to_dict()

        id = self.id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type,
                "function": function,
                "id": id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.function_call_option import FunctionCallOption

        d = src_dict.copy()
        type = ChosenFunctionCallType(d.pop("type"))

        function = FunctionCallOption.from_dict(d.pop("function"))

        id = d.pop("id")

        chosen_function_call = cls(
            type=type,
            function=function,
            id=id,
        )

        chosen_function_call.additional_properties = d
        return chosen_function_call

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
