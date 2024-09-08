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
    from ..models.chat_token_log_prob import ChatTokenLogProb


T = TypeVar("T", bound="LogProbResponse")


@_attrs_define
class LogProbResponse:
    """
    Attributes:
        content (Union[List['ChatTokenLogProb'], None]): The log probabilities of the tokens
    """

    content: Union[List["ChatTokenLogProb"], None]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.chat_token_log_prob import ChatTokenLogProb

        content: Union[List[Dict[str, Any]], None]
        if isinstance(self.content, list):
            content = []
            for content_type_0_item_data in self.content:
                content_type_0_item = content_type_0_item_data.to_dict()
                content.append(content_type_0_item)

        else:
            content = self.content

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "content": content,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.chat_token_log_prob import ChatTokenLogProb

        d = src_dict.copy()

        def _parse_content(data: object) -> Union[List["ChatTokenLogProb"], None]:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                content_type_0 = []
                _content_type_0 = data
                for content_type_0_item_data in _content_type_0:
                    content_type_0_item = ChatTokenLogProb.from_dict(
                        content_type_0_item_data
                    )

                    content_type_0.append(content_type_0_item)

                return content_type_0
            except:  # noqa: E722
                pass
            return cast(Union[List["ChatTokenLogProb"], None], data)

        content = _parse_content(d.pop("content"))

        log_prob_response = cls(
            content=content,
        )

        log_prob_response.additional_properties = d
        return log_prob_response

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
