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

from ..models.evaluate_step_kind import EvaluateStepKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.evaluate_step_evaluate import EvaluateStepEvaluate


T = TypeVar("T", bound="EvaluateStep")


@_attrs_define
class EvaluateStep:
    """
    Attributes:
        kind (EvaluateStepKind): The kind of step
        evaluate (EvaluateStepEvaluate): The expression to evaluate
    """

    kind: EvaluateStepKind
    evaluate: "EvaluateStepEvaluate"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.evaluate_step_evaluate import EvaluateStepEvaluate

        kind = self.kind.value

        evaluate = self.evaluate.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "evaluate": evaluate,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.evaluate_step_evaluate import EvaluateStepEvaluate

        d = src_dict.copy()
        kind = EvaluateStepKind(d.pop("kind_"))

        evaluate = EvaluateStepEvaluate.from_dict(d.pop("evaluate"))

        evaluate_step = cls(
            kind=kind,
            evaluate=evaluate,
        )

        evaluate_step.additional_properties = d
        return evaluate_step

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
