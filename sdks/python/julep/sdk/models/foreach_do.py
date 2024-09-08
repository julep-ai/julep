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
    from ..models.embed_step import EmbedStep
    from ..models.evaluate_step import EvaluateStep
    from ..models.get_step import GetStep
    from ..models.log_step import LogStep
    from ..models.prompt_step import PromptStep
    from ..models.search_step import SearchStep
    from ..models.set_step import SetStep
    from ..models.tool_call_step import ToolCallStep


T = TypeVar("T", bound="ForeachDo")


@_attrs_define
class ForeachDo:
    """
    Attributes:
        in_ (str): A simple python expression compatible with SimpleEval.
        do (Union['EmbedStep', 'EvaluateStep', 'GetStep', 'LogStep', 'PromptStep', 'SearchStep', 'SetStep',
            'ToolCallStep']): The steps to run for each iteration
    """

    in_: str
    do: Union[
        "EmbedStep",
        "EvaluateStep",
        "GetStep",
        "LogStep",
        "PromptStep",
        "SearchStep",
        "SetStep",
        "ToolCallStep",
    ]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.embed_step import EmbedStep
        from ..models.evaluate_step import EvaluateStep
        from ..models.get_step import GetStep
        from ..models.log_step import LogStep
        from ..models.prompt_step import PromptStep
        from ..models.search_step import SearchStep
        from ..models.set_step import SetStep
        from ..models.tool_call_step import ToolCallStep

        in_ = self.in_

        do: Dict[str, Any]
        if isinstance(self.do, EvaluateStep):
            do = self.do.to_dict()
        elif isinstance(self.do, ToolCallStep):
            do = self.do.to_dict()
        elif isinstance(self.do, PromptStep):
            do = self.do.to_dict()
        elif isinstance(self.do, GetStep):
            do = self.do.to_dict()
        elif isinstance(self.do, SetStep):
            do = self.do.to_dict()
        elif isinstance(self.do, LogStep):
            do = self.do.to_dict()
        elif isinstance(self.do, EmbedStep):
            do = self.do.to_dict()
        else:
            do = self.do.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "in": in_,
                "do": do,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.embed_step import EmbedStep
        from ..models.evaluate_step import EvaluateStep
        from ..models.get_step import GetStep
        from ..models.log_step import LogStep
        from ..models.prompt_step import PromptStep
        from ..models.search_step import SearchStep
        from ..models.set_step import SetStep
        from ..models.tool_call_step import ToolCallStep

        d = src_dict.copy()
        in_ = d.pop("in")

        def _parse_do(
            data: object,
        ) -> Union[
            "EmbedStep",
            "EvaluateStep",
            "GetStep",
            "LogStep",
            "PromptStep",
            "SearchStep",
            "SetStep",
            "ToolCallStep",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                do_type_0 = EvaluateStep.from_dict(data)

                return do_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                do_type_1 = ToolCallStep.from_dict(data)

                return do_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                do_type_2 = PromptStep.from_dict(data)

                return do_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                do_type_3 = GetStep.from_dict(data)

                return do_type_3
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                do_type_4 = SetStep.from_dict(data)

                return do_type_4
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                do_type_5 = LogStep.from_dict(data)

                return do_type_5
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                do_type_6 = EmbedStep.from_dict(data)

                return do_type_6
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            do_type_7 = SearchStep.from_dict(data)

            return do_type_7

        do = _parse_do(d.pop("do"))

        foreach_do = cls(
            in_=in_,
            do=do,
        )

        foreach_do.additional_properties = d
        return foreach_do

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
