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

from ..models.yield_step_arguments_type_1 import YieldStepArgumentsType1
from ..models.yield_step_kind import YieldStepKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.yield_step_arguments_type_0 import YieldStepArgumentsType0


T = TypeVar("T", bound="YieldStep")


@_attrs_define
class YieldStep:
    """
    Attributes:
        kind (YieldStepKind): The kind of step
        workflow (str): The subworkflow to run.
            VALIDATION: Should resolve to a defined subworkflow.
        arguments (Union['YieldStepArgumentsType0', YieldStepArgumentsType1]): The input parameters for the subworkflow
            (defaults to last step output) Default: YieldStepArgumentsType1.VALUE_0.
    """

    kind: YieldStepKind
    workflow: str
    arguments: Union["YieldStepArgumentsType0", YieldStepArgumentsType1] = (
        YieldStepArgumentsType1.VALUE_0
    )
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.yield_step_arguments_type_0 import YieldStepArgumentsType0

        kind = self.kind.value

        workflow = self.workflow

        arguments: Union[Dict[str, Any], str]
        if isinstance(self.arguments, YieldStepArgumentsType0):
            arguments = self.arguments.to_dict()
        else:
            arguments = self.arguments.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "workflow": workflow,
                "arguments": arguments,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.yield_step_arguments_type_0 import YieldStepArgumentsType0

        d = src_dict.copy()
        kind = YieldStepKind(d.pop("kind_"))

        workflow = d.pop("workflow")

        def _parse_arguments(
            data: object,
        ) -> Union["YieldStepArgumentsType0", YieldStepArgumentsType1]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                arguments_type_0 = YieldStepArgumentsType0.from_dict(data)

                return arguments_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, str):
                raise TypeError()
            arguments_type_1 = YieldStepArgumentsType1(data)

            return arguments_type_1

        arguments = _parse_arguments(d.pop("arguments"))

        yield_step = cls(
            kind=kind,
            workflow=workflow,
            arguments=arguments,
        )

        yield_step.additional_properties = d
        return yield_step

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
