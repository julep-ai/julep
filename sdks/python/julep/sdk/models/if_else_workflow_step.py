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

from ..models.if_else_workflow_step_kind import IfElseWorkflowStepKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.embed_step import EmbedStep
    from ..models.error_workflow_step import ErrorWorkflowStep
    from ..models.evaluate_step import EvaluateStep
    from ..models.get_step import GetStep
    from ..models.log_step import LogStep
    from ..models.prompt_step import PromptStep
    from ..models.return_step import ReturnStep
    from ..models.search_step import SearchStep
    from ..models.set_step import SetStep
    from ..models.sleep_step import SleepStep
    from ..models.tool_call_step import ToolCallStep
    from ..models.wait_for_input_step import WaitForInputStep
    from ..models.yield_step import YieldStep


T = TypeVar("T", bound="IfElseWorkflowStep")


@_attrs_define
class IfElseWorkflowStep:
    """
    Attributes:
        kind (IfElseWorkflowStepKind): The kind of step
        if_ (str): A simple python expression compatible with SimpleEval.
        then (Union['EmbedStep', 'ErrorWorkflowStep', 'EvaluateStep', 'GetStep', 'LogStep', 'PromptStep', 'ReturnStep',
            'SearchStep', 'SetStep', 'SleepStep', 'ToolCallStep', 'WaitForInputStep', 'YieldStep']): The steps to run if the
            condition is true
        else_ (Union['EmbedStep', 'ErrorWorkflowStep', 'EvaluateStep', 'GetStep', 'LogStep', 'PromptStep', 'ReturnStep',
            'SearchStep', 'SetStep', 'SleepStep', 'ToolCallStep', 'WaitForInputStep', 'YieldStep', None]): The steps to run
            if the condition is false
    """

    kind: IfElseWorkflowStepKind
    if_: str
    then: Union[
        "EmbedStep",
        "ErrorWorkflowStep",
        "EvaluateStep",
        "GetStep",
        "LogStep",
        "PromptStep",
        "ReturnStep",
        "SearchStep",
        "SetStep",
        "SleepStep",
        "ToolCallStep",
        "WaitForInputStep",
        "YieldStep",
    ]
    else_: Union[
        "EmbedStep",
        "ErrorWorkflowStep",
        "EvaluateStep",
        "GetStep",
        "LogStep",
        "PromptStep",
        "ReturnStep",
        "SearchStep",
        "SetStep",
        "SleepStep",
        "ToolCallStep",
        "WaitForInputStep",
        "YieldStep",
        None,
    ]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.embed_step import EmbedStep
        from ..models.error_workflow_step import ErrorWorkflowStep
        from ..models.evaluate_step import EvaluateStep
        from ..models.get_step import GetStep
        from ..models.log_step import LogStep
        from ..models.prompt_step import PromptStep
        from ..models.return_step import ReturnStep
        from ..models.search_step import SearchStep
        from ..models.set_step import SetStep
        from ..models.sleep_step import SleepStep
        from ..models.tool_call_step import ToolCallStep
        from ..models.wait_for_input_step import WaitForInputStep
        from ..models.yield_step import YieldStep

        kind = self.kind.value

        if_ = self.if_

        then: Dict[str, Any]
        if isinstance(self.then, EvaluateStep):
            then = self.then.to_dict()
        elif isinstance(self.then, ToolCallStep):
            then = self.then.to_dict()
        elif isinstance(self.then, PromptStep):
            then = self.then.to_dict()
        elif isinstance(self.then, GetStep):
            then = self.then.to_dict()
        elif isinstance(self.then, SetStep):
            then = self.then.to_dict()
        elif isinstance(self.then, LogStep):
            then = self.then.to_dict()
        elif isinstance(self.then, EmbedStep):
            then = self.then.to_dict()
        elif isinstance(self.then, SearchStep):
            then = self.then.to_dict()
        elif isinstance(self.then, ReturnStep):
            then = self.then.to_dict()
        elif isinstance(self.then, SleepStep):
            then = self.then.to_dict()
        elif isinstance(self.then, ErrorWorkflowStep):
            then = self.then.to_dict()
        elif isinstance(self.then, YieldStep):
            then = self.then.to_dict()
        else:
            then = self.then.to_dict()

        else_: Union[Dict[str, Any], None]
        if isinstance(self.else_, EvaluateStep):
            else_ = self.else_.to_dict()
        elif isinstance(self.else_, ToolCallStep):
            else_ = self.else_.to_dict()
        elif isinstance(self.else_, PromptStep):
            else_ = self.else_.to_dict()
        elif isinstance(self.else_, GetStep):
            else_ = self.else_.to_dict()
        elif isinstance(self.else_, SetStep):
            else_ = self.else_.to_dict()
        elif isinstance(self.else_, LogStep):
            else_ = self.else_.to_dict()
        elif isinstance(self.else_, EmbedStep):
            else_ = self.else_.to_dict()
        elif isinstance(self.else_, SearchStep):
            else_ = self.else_.to_dict()
        elif isinstance(self.else_, ReturnStep):
            else_ = self.else_.to_dict()
        elif isinstance(self.else_, SleepStep):
            else_ = self.else_.to_dict()
        elif isinstance(self.else_, ErrorWorkflowStep):
            else_ = self.else_.to_dict()
        elif isinstance(self.else_, YieldStep):
            else_ = self.else_.to_dict()
        elif isinstance(self.else_, WaitForInputStep):
            else_ = self.else_.to_dict()
        else:
            else_ = self.else_

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "if": if_,
                "then": then,
                "else": else_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.embed_step import EmbedStep
        from ..models.error_workflow_step import ErrorWorkflowStep
        from ..models.evaluate_step import EvaluateStep
        from ..models.get_step import GetStep
        from ..models.log_step import LogStep
        from ..models.prompt_step import PromptStep
        from ..models.return_step import ReturnStep
        from ..models.search_step import SearchStep
        from ..models.set_step import SetStep
        from ..models.sleep_step import SleepStep
        from ..models.tool_call_step import ToolCallStep
        from ..models.wait_for_input_step import WaitForInputStep
        from ..models.yield_step import YieldStep

        d = src_dict.copy()
        kind = IfElseWorkflowStepKind(d.pop("kind_"))

        if_ = d.pop("if")

        def _parse_then(
            data: object,
        ) -> Union[
            "EmbedStep",
            "ErrorWorkflowStep",
            "EvaluateStep",
            "GetStep",
            "LogStep",
            "PromptStep",
            "ReturnStep",
            "SearchStep",
            "SetStep",
            "SleepStep",
            "ToolCallStep",
            "WaitForInputStep",
            "YieldStep",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                then_type_0 = EvaluateStep.from_dict(data)

                return then_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                then_type_1 = ToolCallStep.from_dict(data)

                return then_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                then_type_2 = PromptStep.from_dict(data)

                return then_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                then_type_3 = GetStep.from_dict(data)

                return then_type_3
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                then_type_4 = SetStep.from_dict(data)

                return then_type_4
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                then_type_5 = LogStep.from_dict(data)

                return then_type_5
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                then_type_6 = EmbedStep.from_dict(data)

                return then_type_6
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                then_type_7 = SearchStep.from_dict(data)

                return then_type_7
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                then_type_8 = ReturnStep.from_dict(data)

                return then_type_8
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                then_type_9 = SleepStep.from_dict(data)

                return then_type_9
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                then_type_10 = ErrorWorkflowStep.from_dict(data)

                return then_type_10
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                then_type_11 = YieldStep.from_dict(data)

                return then_type_11
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            then_type_12 = WaitForInputStep.from_dict(data)

            return then_type_12

        then = _parse_then(d.pop("then"))

        def _parse_else_(
            data: object,
        ) -> Union[
            "EmbedStep",
            "ErrorWorkflowStep",
            "EvaluateStep",
            "GetStep",
            "LogStep",
            "PromptStep",
            "ReturnStep",
            "SearchStep",
            "SetStep",
            "SleepStep",
            "ToolCallStep",
            "WaitForInputStep",
            "YieldStep",
            None,
        ]:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_0 = EvaluateStep.from_dict(data)

                return else_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_1 = ToolCallStep.from_dict(data)

                return else_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_2 = PromptStep.from_dict(data)

                return else_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_3 = GetStep.from_dict(data)

                return else_type_3
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_4 = SetStep.from_dict(data)

                return else_type_4
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_5 = LogStep.from_dict(data)

                return else_type_5
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_6 = EmbedStep.from_dict(data)

                return else_type_6
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_7 = SearchStep.from_dict(data)

                return else_type_7
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_8 = ReturnStep.from_dict(data)

                return else_type_8
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_9 = SleepStep.from_dict(data)

                return else_type_9
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_10 = ErrorWorkflowStep.from_dict(data)

                return else_type_10
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_11 = YieldStep.from_dict(data)

                return else_type_11
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                else_type_12 = WaitForInputStep.from_dict(data)

                return else_type_12
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    "EmbedStep",
                    "ErrorWorkflowStep",
                    "EvaluateStep",
                    "GetStep",
                    "LogStep",
                    "PromptStep",
                    "ReturnStep",
                    "SearchStep",
                    "SetStep",
                    "SleepStep",
                    "ToolCallStep",
                    "WaitForInputStep",
                    "YieldStep",
                    None,
                ],
                data,
            )

        else_ = _parse_else_(d.pop("else"))

        if_else_workflow_step = cls(
            kind=kind,
            if_=if_,
            then=then,
            else_=else_,
        )

        if_else_workflow_step.additional_properties = d
        return if_else_workflow_step

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
