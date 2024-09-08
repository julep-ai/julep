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
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.prompt_step_prompt_type_1_item_content_type_2_item_type_1_type import (
    PromptStepPromptType1ItemContentType2ItemType1Type,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.prompt_step_prompt_type_1_item_content_type_2_item_type_1_image_url import (
        PromptStepPromptType1ItemContentType2ItemType1ImageUrl,
    )


T = TypeVar("T", bound="PromptStepPromptType1ItemContentType2ItemType1")


@_attrs_define
class PromptStepPromptType1ItemContentType2ItemType1:
    """
    Attributes:
        image_url (PromptStepPromptType1ItemContentType2ItemType1ImageUrl): The image URL
        type (PromptStepPromptType1ItemContentType2ItemType1Type): The type (fixed to 'image_url') Default:
            PromptStepPromptType1ItemContentType2ItemType1Type.IMAGE_URL.
    """

    image_url: "PromptStepPromptType1ItemContentType2ItemType1ImageUrl"
    type: PromptStepPromptType1ItemContentType2ItemType1Type = (
        PromptStepPromptType1ItemContentType2ItemType1Type.IMAGE_URL
    )
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.prompt_step_prompt_type_1_item_content_type_2_item_type_1_image_url import (
            PromptStepPromptType1ItemContentType2ItemType1ImageUrl,
        )

        image_url = self.image_url.to_dict()

        type = self.type.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "image_url": image_url,
                "type": type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.prompt_step_prompt_type_1_item_content_type_2_item_type_1_image_url import (
            PromptStepPromptType1ItemContentType2ItemType1ImageUrl,
        )

        d = src_dict.copy()
        image_url = PromptStepPromptType1ItemContentType2ItemType1ImageUrl.from_dict(
            d.pop("image_url")
        )

        type = PromptStepPromptType1ItemContentType2ItemType1Type(d.pop("type"))

        prompt_step_prompt_type_1_item_content_type_2_item_type_1 = cls(
            image_url=image_url,
            type=type,
        )

        prompt_step_prompt_type_1_item_content_type_2_item_type_1.additional_properties = d
        return prompt_step_prompt_type_1_item_content_type_2_item_type_1

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
