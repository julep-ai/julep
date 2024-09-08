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

from ..models.tool_call_step_arguments_type_1 import ToolCallStepArgumentsType1
from ..models.tool_call_step_kind import ToolCallStepKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tool_call_step_arguments_type_0 import ToolCallStepArgumentsType0


T = TypeVar("T", bound="ToolCallStep")


@_attrs_define
class ToolCallStep:
    """
    Attributes:
        kind (ToolCallStepKind): The kind of step
        tool (str): Naming convention for tool references. Tools are resolved in order: `step-settings` -> `task` ->
            `agent`
        arguments (Union['ToolCallStepArgumentsType0', ToolCallStepArgumentsType1]): The input parameters for the tool
            (defaults to last step output) Default: ToolCallStepArgumentsType1.VALUE_0.
    """

    kind: ToolCallStepKind
    tool: str
    arguments: Union["ToolCallStepArgumentsType0", ToolCallStepArgumentsType1] = (
        ToolCallStepArgumentsType1.VALUE_0
    )
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.tool_call_step_arguments_type_0 import ToolCallStepArgumentsType0

        kind = self.kind.value

        tool = self.tool

        arguments: Union[Dict[str, Any], str]
        if isinstance(self.arguments, ToolCallStepArgumentsType0):
            arguments = self.arguments.to_dict()
        else:
            arguments = self.arguments.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "tool": tool,
                "arguments": arguments,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.tool_call_step_arguments_type_0 import ToolCallStepArgumentsType0

        d = src_dict.copy()
        kind = ToolCallStepKind(d.pop("kind_"))

        tool = d.pop("tool")

        def _parse_arguments(
            data: object,
        ) -> Union["ToolCallStepArgumentsType0", ToolCallStepArgumentsType1]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                arguments_type_0 = ToolCallStepArgumentsType0.from_dict(data)

                return arguments_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, str):
                raise TypeError()
            arguments_type_1 = ToolCallStepArgumentsType1(data)

            return arguments_type_1

        arguments = _parse_arguments(d.pop("arguments"))

        tool_call_step = cls(
            kind=kind,
            tool=tool,
            arguments=arguments,
        )

        tool_call_step.additional_properties = d
        return tool_call_step

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
