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
    from ..models.base_agent_metadata import BaseAgentMetadata
    from ..models.default_chat_settings import DefaultChatSettings


T = TypeVar("T", bound="BaseAgent")


@_attrs_define
class BaseAgent:
    """
    Attributes:
        name (str): For Unicode character safety
            See: https://unicode.org/reports/tr31/
            See: https://www.unicode.org/reports/tr39/#Identifier_Characters Default: ''.
        about (str): About the agent Default: ''.
        model (str): Model name to use (gpt-4-turbo, gemini-nano etc) Default: ''.
        instructions (Union[List[str], str]): Instructions for the agent Default: '[]'.
        metadata (Union[Unset, BaseAgentMetadata]):
        default_settings (Union[Unset, DefaultChatSettings]): Default settings for the chat session (also used by the
            agent)
    """

    name: str = ""
    about: str = ""
    model: str = ""
    instructions: Union[List[str], str] = "[]"
    metadata: Union[Unset, "BaseAgentMetadata"] = UNSET
    default_settings: Union[Unset, "DefaultChatSettings"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.base_agent_metadata import BaseAgentMetadata
        from ..models.default_chat_settings import DefaultChatSettings

        name = self.name

        about = self.about

        model = self.model

        instructions: Union[List[str], str]
        if isinstance(self.instructions, list):
            instructions = self.instructions

        else:
            instructions = self.instructions

        metadata: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        default_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.default_settings, Unset):
            default_settings = self.default_settings.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "about": about,
                "model": model,
                "instructions": instructions,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if default_settings is not UNSET:
            field_dict["default_settings"] = default_settings

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.base_agent_metadata import BaseAgentMetadata
        from ..models.default_chat_settings import DefaultChatSettings

        d = src_dict.copy()
        name = d.pop("name")

        about = d.pop("about")

        model = d.pop("model")

        def _parse_instructions(data: object) -> Union[List[str], str]:
            try:
                if not isinstance(data, list):
                    raise TypeError()
                instructions_type_1 = cast(List[str], data)

                return instructions_type_1
            except:  # noqa: E722
                pass
            return cast(Union[List[str], str], data)

        instructions = _parse_instructions(d.pop("instructions"))

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, BaseAgentMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = BaseAgentMetadata.from_dict(_metadata)

        _default_settings = d.pop("default_settings", UNSET)
        default_settings: Union[Unset, DefaultChatSettings]
        if isinstance(_default_settings, Unset):
            default_settings = UNSET
        else:
            default_settings = DefaultChatSettings.from_dict(_default_settings)

        base_agent = cls(
            name=name,
            about=about,
            model=model,
            instructions=instructions,
            metadata=metadata,
            default_settings=default_settings,
        )

        base_agent.additional_properties = d
        return base_agent

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
