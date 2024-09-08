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

from ..models.entries_image_detail import EntriesImageDetail
from ..types import UNSET, Unset

T = TypeVar("T", bound="ChatInputDataMessagesItemContentType2ItemType1ImageUrl")


@_attrs_define
class ChatInputDataMessagesItemContentType2ItemType1ImageUrl:
    """The image URL

    Attributes:
        url (str): Image URL or base64 data url (e.g. `data:image/jpeg;base64,<the base64 encoded image>`)
        detail (EntriesImageDetail): Image detail level Default: EntriesImageDetail.AUTO.
    """

    url: str
    detail: EntriesImageDetail = EntriesImageDetail.AUTO
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        url = self.url

        detail = self.detail.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "url": url,
                "detail": detail,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        url = d.pop("url")

        detail = EntriesImageDetail(d.pop("detail"))

        chat_input_data_messages_item_content_type_2_item_type_1_image_url = cls(
            url=url,
            detail=detail,
        )

        chat_input_data_messages_item_content_type_2_item_type_1_image_url.additional_properties = d
        return chat_input_data_messages_item_content_type_2_item_type_1_image_url

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
