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
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.chat_input_messages_item_content_type_2_item_type_0_type import (
    ChatInputMessagesItemContentType2ItemType0Type,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="ChatInputMessagesItemContentType2ItemType0")


@_attrs_define
class ChatInputMessagesItemContentType2ItemType0:
    """
    Attributes:
        text (str):
        type (ChatInputMessagesItemContentType2ItemType0Type): The type (fixed to 'text') Default:
            ChatInputMessagesItemContentType2ItemType0Type.TEXT.
    """

    text: str
    type: ChatInputMessagesItemContentType2ItemType0Type = (
        ChatInputMessagesItemContentType2ItemType0Type.TEXT
    )
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        text = self.text

        type = self.type.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "text": text,
                "type": type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        text = d.pop("text")

        type = ChatInputMessagesItemContentType2ItemType0Type(d.pop("type"))

        chat_input_messages_item_content_type_2_item_type_0 = cls(
            text=text,
            type=type,
        )

        chat_input_messages_item_content_type_2_item_type_0.additional_properties = d
        return chat_input_messages_item_content_type_2_item_type_0

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
