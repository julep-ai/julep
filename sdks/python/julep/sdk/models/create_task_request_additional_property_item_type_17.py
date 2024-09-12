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

from ..models.create_task_request_additional_property_item_type_17_kind import (
    CreateTaskRequestAdditionalPropertyItemType17Kind,
)
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


T = TypeVar("T", bound="CreateTaskRequestAdditionalPropertyItemType17")


@_attrs_define
class CreateTaskRequestAdditionalPropertyItemType17:
    """
    Attributes:
        kind (CreateTaskRequestAdditionalPropertyItemType17Kind): The kind of step Default:
            CreateTaskRequestAdditionalPropertyItemType17Kind.MAP_REDUCE.
        over (str): A simple python expression compatible with SimpleEval.
        map_ (Union['EmbedStep', 'EvaluateStep', 'GetStep', 'LogStep', 'PromptStep', 'SearchStep', 'SetStep',
            'ToolCallStep']): The steps to run for each iteration
        reduce (Union[Unset, str]): A simple python expression compatible with SimpleEval.
        initial (Union[Unset, Any]): The initial value of the reduce expression Default: [].
        parallelism (Union[Unset, int]): Whether to run the reduce expression in parallel and how many items to run in
            each batch
    """

    over: str
    map_: Union[
        "EmbedStep",
        "EvaluateStep",
        "GetStep",
        "LogStep",
        "PromptStep",
        "SearchStep",
        "SetStep",
        "ToolCallStep",
    ]
    kind: CreateTaskRequestAdditionalPropertyItemType17Kind = (
        CreateTaskRequestAdditionalPropertyItemType17Kind.MAP_REDUCE
    )
    reduce: Union[Unset, str] = UNSET
    initial: Union[Unset, Any] = []
    parallelism: Union[Unset, int] = UNSET
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

        over = self.over

        map_: Dict[str, Any]
        if isinstance(self.map_, EvaluateStep):
            map_ = self.map_.to_dict()
        elif isinstance(self.map_, ToolCallStep):
            map_ = self.map_.to_dict()
        elif isinstance(self.map_, PromptStep):
            map_ = self.map_.to_dict()
        elif isinstance(self.map_, GetStep):
            map_ = self.map_.to_dict()
        elif isinstance(self.map_, SetStep):
            map_ = self.map_.to_dict()
        elif isinstance(self.map_, LogStep):
            map_ = self.map_.to_dict()
        elif isinstance(self.map_, EmbedStep):
            map_ = self.map_.to_dict()
        else:
            map_ = self.map_.to_dict()

        reduce = self.reduce

        initial = self.initial

        parallelism = self.parallelism

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "over": over,
                "map": map_,
            }
        )
        if reduce is not UNSET:
            field_dict["reduce"] = reduce
        if initial is not UNSET:
            field_dict["initial"] = initial
        if parallelism is not UNSET:
            field_dict["parallelism"] = parallelism

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
        kind = CreateTaskRequestAdditionalPropertyItemType17Kind(d.pop("kind_"))

        over = d.pop("over")

        def _parse_map_(
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
                map_type_0 = EvaluateStep.from_dict(data)

                return map_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                map_type_1 = ToolCallStep.from_dict(data)

                return map_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                map_type_2 = PromptStep.from_dict(data)

                return map_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                map_type_3 = GetStep.from_dict(data)

                return map_type_3
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                map_type_4 = SetStep.from_dict(data)

                return map_type_4
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                map_type_5 = LogStep.from_dict(data)

                return map_type_5
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                map_type_6 = EmbedStep.from_dict(data)

                return map_type_6
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            map_type_7 = SearchStep.from_dict(data)

            return map_type_7

        map_ = _parse_map_(d.pop("map"))

        reduce = d.pop("reduce", UNSET)

        initial = d.pop("initial", UNSET)

        parallelism = d.pop("parallelism", UNSET)

        create_task_request_additional_property_item_type_17 = cls(
            kind=kind,
            over=over,
            map_=map_,
            reduce=reduce,
            initial=initial,
            parallelism=parallelism,
        )

        create_task_request_additional_property_item_type_17.additional_properties = d
        return create_task_request_additional_property_item_type_17

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
