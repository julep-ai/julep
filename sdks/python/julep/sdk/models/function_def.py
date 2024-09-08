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
    from ..models.function_def_parameters import FunctionDefParameters


T = TypeVar("T", bound="FunctionDef")


@_attrs_define
class FunctionDef:
    """Function definition

    Attributes:
        name (Union[Unset, Any]): DO NOT USE: This will be overriden by the tool name. Here only for compatibility
            reasons.
        description (Union[Unset, str]): For Unicode character safety
            See: https://unicode.org/reports/tr31/
            See: https://www.unicode.org/reports/tr39/#Identifier_Characters
        parameters (Union[Unset, FunctionDefParameters]): The parameters the function accepts
    """

    name: Union[Unset, Any] = UNSET
    description: Union[Unset, str] = UNSET
    parameters: Union[Unset, "FunctionDefParameters"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.function_def_parameters import FunctionDefParameters

        name = self.name

        description = self.description

        parameters: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = self.parameters.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if parameters is not UNSET:
            field_dict["parameters"] = parameters

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.function_def_parameters import FunctionDefParameters

        d = src_dict.copy()
        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        _parameters = d.pop("parameters", UNSET)
        parameters: Union[Unset, FunctionDefParameters]
        if isinstance(_parameters, Unset):
            parameters = UNSET
        else:
            parameters = FunctionDefParameters.from_dict(_parameters)

        function_def = cls(
            name=name,
            description=description,
            parameters=parameters,
        )

        function_def.additional_properties = d
        return function_def

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
