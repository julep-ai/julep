import datetime
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
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_metadata import AgentMetadata
    from ..models.chat_open_ai_settings import ChatOpenAISettings


T = TypeVar("T", bound="Agent")


@_attrs_define
class Agent:
    """
    Attributes:
        name (str): For Unicode character safety
            See: https://unicode.org/reports/tr31/
            See: https://www.unicode.org/reports/tr39/#Identifier_Characters Default: ''.
        about (str): About the agent Default: ''.
        model (str): Model name to use (gpt-4-turbo, gemini-nano etc) Default: ''.
        instructions (Union[List[str], str]): Instructions for the agent Default: '[]'.
        id (str):
        created_at (datetime.datetime): When this resource was created as UTC date-time
        updated_at (datetime.datetime): When this resource was updated as UTC date-time
        metadata (Union[Unset, AgentMetadata]):
        default_settings (Union[Unset, ChatOpenAISettings]):
    """

    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    name: str = ""
    about: str = ""
    model: str = ""
    instructions: Union[List[str], str] = "[]"
    metadata: Union[Unset, "AgentMetadata"] = UNSET
    default_settings: Union[Unset, "ChatOpenAISettings"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.agent_metadata import AgentMetadata
        from ..models.chat_open_ai_settings import ChatOpenAISettings

        name = self.name

        about = self.about

        model = self.model

        instructions: Union[List[str], str]
        if isinstance(self.instructions, list):
            instructions = self.instructions

        else:
            instructions = self.instructions

        id = self.id

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

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
                "id": id,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if default_settings is not UNSET:
            field_dict["default_settings"] = default_settings

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.agent_metadata import AgentMetadata
        from ..models.chat_open_ai_settings import ChatOpenAISettings

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

        id = d.pop("id")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, AgentMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = AgentMetadata.from_dict(_metadata)

        _default_settings = d.pop("default_settings", UNSET)
        default_settings: Union[Unset, ChatOpenAISettings]
        if isinstance(_default_settings, Unset):
            default_settings = UNSET
        else:
            default_settings = ChatOpenAISettings.from_dict(_default_settings)

        agent = cls(
            name=name,
            about=about,
            model=model,
            instructions=instructions,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            metadata=metadata,
            default_settings=default_settings,
        )

        agent.additional_properties = d
        return agent

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
