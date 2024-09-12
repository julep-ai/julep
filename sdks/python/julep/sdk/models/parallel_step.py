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

from ..models.parallel_step_kind import ParallelStepKind
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


T = TypeVar("T", bound="ParallelStep")


@_attrs_define
class ParallelStep:
    """
    Attributes:
        kind (ParallelStepKind): The kind of step Default: ParallelStepKind.PARALLEL.
        parallel (List[Union['EmbedStep', 'EvaluateStep', 'GetStep', 'LogStep', 'PromptStep', 'SearchStep', 'SetStep',
            'ToolCallStep']]): The steps to run in parallel. Max concurrency will depend on the platform.
    """

    parallel: List[
        Union[
            "EmbedStep",
            "EvaluateStep",
            "GetStep",
            "LogStep",
            "PromptStep",
            "SearchStep",
            "SetStep",
            "ToolCallStep",
        ]
    ]
    kind: ParallelStepKind = ParallelStepKind.PARALLEL
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

        kind = self.kind.value

        parallel = []
        for parallel_item_data in self.parallel:
            parallel_item: Dict[str, Any]
            if isinstance(parallel_item_data, EvaluateStep):
                parallel_item = parallel_item_data.to_dict()
            elif isinstance(parallel_item_data, ToolCallStep):
                parallel_item = parallel_item_data.to_dict()
            elif isinstance(parallel_item_data, PromptStep):
                parallel_item = parallel_item_data.to_dict()
            elif isinstance(parallel_item_data, GetStep):
                parallel_item = parallel_item_data.to_dict()
            elif isinstance(parallel_item_data, SetStep):
                parallel_item = parallel_item_data.to_dict()
            elif isinstance(parallel_item_data, LogStep):
                parallel_item = parallel_item_data.to_dict()
            elif isinstance(parallel_item_data, EmbedStep):
                parallel_item = parallel_item_data.to_dict()
            else:
                parallel_item = parallel_item_data.to_dict()

            parallel.append(parallel_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "parallel": parallel,
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
        kind = ParallelStepKind(d.pop("kind_"))

        parallel = []
        _parallel = d.pop("parallel")
        for parallel_item_data in _parallel:

            def _parse_parallel_item(
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
                    parallel_item_type_0 = EvaluateStep.from_dict(data)

                    return parallel_item_type_0
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    parallel_item_type_1 = ToolCallStep.from_dict(data)

                    return parallel_item_type_1
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    parallel_item_type_2 = PromptStep.from_dict(data)

                    return parallel_item_type_2
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    parallel_item_type_3 = GetStep.from_dict(data)

                    return parallel_item_type_3
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    parallel_item_type_4 = SetStep.from_dict(data)

                    return parallel_item_type_4
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    parallel_item_type_5 = LogStep.from_dict(data)

                    return parallel_item_type_5
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    parallel_item_type_6 = EmbedStep.from_dict(data)

                    return parallel_item_type_6
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                parallel_item_type_7 = SearchStep.from_dict(data)

                return parallel_item_type_7

            parallel_item = _parse_parallel_item(parallel_item_data)

            parallel.append(parallel_item)

        parallel_step = cls(
            kind=kind,
            parallel=parallel,
        )

        parallel_step.additional_properties = d
        return parallel_step

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
