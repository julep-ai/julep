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

from ..models.prompt_step_kind import PromptStepKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_settings import ChatSettings
    from ..models.prompt_step_prompt_type_1_item import PromptStepPromptType1Item


T = TypeVar("T", bound="PromptStep")


@_attrs_define
class PromptStep:
    """
    Attributes:
        kind (PromptStepKind): The kind of step
        prompt (Union[List['PromptStepPromptType1Item'], str]): The prompt to run
        settings (Union[Unset, ChatSettings]):
    """

    kind: PromptStepKind
    prompt: Union[List["PromptStepPromptType1Item"], str]
    settings: Union[Unset, "ChatSettings"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.chat_settings import ChatSettings
        from ..models.prompt_step_prompt_type_1_item import PromptStepPromptType1Item

        kind = self.kind.value

        prompt: Union[List[Dict[str, Any]], str]
        if isinstance(self.prompt, list):
            prompt = []
            for prompt_type_1_item_data in self.prompt:
                prompt_type_1_item = prompt_type_1_item_data.to_dict()
                prompt.append(prompt_type_1_item)

        else:
            prompt = self.prompt

        settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.settings, Unset):
            settings = self.settings.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "prompt": prompt,
            }
        )
        if settings is not UNSET:
            field_dict["settings"] = settings

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.chat_settings import ChatSettings
        from ..models.prompt_step_prompt_type_1_item import PromptStepPromptType1Item

        d = src_dict.copy()
        kind = PromptStepKind(d.pop("kind_"))

        def _parse_prompt(
            data: object,
        ) -> Union[List["PromptStepPromptType1Item"], str]:
            try:
                if not isinstance(data, list):
                    raise TypeError()
                prompt_type_1 = []
                _prompt_type_1 = data
                for prompt_type_1_item_data in _prompt_type_1:
                    prompt_type_1_item = PromptStepPromptType1Item.from_dict(
                        prompt_type_1_item_data
                    )

                    prompt_type_1.append(prompt_type_1_item)

                return prompt_type_1
            except:  # noqa: E722
                pass
            return cast(Union[List["PromptStepPromptType1Item"], str], data)

        prompt = _parse_prompt(d.pop("prompt"))

        _settings = d.pop("settings", UNSET)
        settings: Union[Unset, ChatSettings]
        if isinstance(_settings, Unset):
            settings = UNSET
        else:
            settings = ChatSettings.from_dict(_settings)

        prompt_step = cls(
            kind=kind,
            prompt=prompt,
            settings=settings,
        )

        prompt_step.additional_properties = d
        return prompt_step

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
