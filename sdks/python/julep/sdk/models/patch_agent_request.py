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
    from ..models.default_chat_settings import DefaultChatSettings
    from ..models.patch_agent_request_metadata import PatchAgentRequestMetadata


T = TypeVar("T", bound="PatchAgentRequest")


@_attrs_define
class PatchAgentRequest:
    """Payload for patching a agent

    Attributes:
        metadata (Union[Unset, PatchAgentRequestMetadata]):
        name (Union[Unset, str]): For Unicode character safety
            See: https://unicode.org/reports/tr31/
            See: https://www.unicode.org/reports/tr39/#Identifier_Characters Default: ''.
        about (Union[Unset, str]): About the agent Default: ''.
        model (Union[Unset, str]): Model name to use (gpt-4-turbo, gemini-nano etc) Default: ''.
        instructions (Union[List[str], Unset, str]): Instructions for the agent Default: '[]'.
        default_settings (Union[Unset, DefaultChatSettings]): Default settings for the chat session (also used by the
            agent)
    """

    metadata: Union[Unset, "PatchAgentRequestMetadata"] = UNSET
    name: Union[Unset, str] = ""
    about: Union[Unset, str] = ""
    model: Union[Unset, str] = ""
    instructions: Union[List[str], Unset, str] = "[]"
    default_settings: Union[Unset, "DefaultChatSettings"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.default_chat_settings import DefaultChatSettings
        from ..models.patch_agent_request_metadata import PatchAgentRequestMetadata

        metadata: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        name = self.name

        about = self.about

        model = self.model

        instructions: Union[List[str], Unset, str]
        if isinstance(self.instructions, Unset):
            instructions = UNSET
        elif isinstance(self.instructions, list):
            instructions = self.instructions

        else:
            instructions = self.instructions

        default_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.default_settings, Unset):
            default_settings = self.default_settings.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if name is not UNSET:
            field_dict["name"] = name
        if about is not UNSET:
            field_dict["about"] = about
        if model is not UNSET:
            field_dict["model"] = model
        if instructions is not UNSET:
            field_dict["instructions"] = instructions
        if default_settings is not UNSET:
            field_dict["default_settings"] = default_settings

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.default_chat_settings import DefaultChatSettings
        from ..models.patch_agent_request_metadata import PatchAgentRequestMetadata

        d = src_dict.copy()
        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, PatchAgentRequestMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = PatchAgentRequestMetadata.from_dict(_metadata)

        name = d.pop("name", UNSET)

        about = d.pop("about", UNSET)

        model = d.pop("model", UNSET)

        def _parse_instructions(data: object) -> Union[List[str], Unset, str]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                instructions_type_1 = cast(List[str], data)

                return instructions_type_1
            except:  # noqa: E722
                pass
            return cast(Union[List[str], Unset, str], data)

        instructions = _parse_instructions(d.pop("instructions", UNSET))

        _default_settings = d.pop("default_settings", UNSET)
        default_settings: Union[Unset, DefaultChatSettings]
        if isinstance(_default_settings, Unset):
            default_settings = UNSET
        else:
            default_settings = DefaultChatSettings.from_dict(_default_settings)

        patch_agent_request = cls(
            metadata=metadata,
            name=name,
            about=about,
            model=model,
            instructions=instructions,
            default_settings=default_settings,
        )

        patch_agent_request.additional_properties = d
        return patch_agent_request

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
