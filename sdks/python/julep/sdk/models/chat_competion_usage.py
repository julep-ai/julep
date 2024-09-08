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
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ChatCompetionUsage")


@_attrs_define
class ChatCompetionUsage:
    """Usage statistics for the completion request

    Attributes:
        completion_tokens (Union[Unset, int]): Number of tokens in the generated completion
        prompt_tokens (Union[Unset, int]): Number of tokens in the prompt
        total_tokens (Union[Unset, int]): Total number of tokens used in the request (prompt + completion)
    """

    completion_tokens: Union[Unset, int] = UNSET
    prompt_tokens: Union[Unset, int] = UNSET
    total_tokens: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        completion_tokens = self.completion_tokens

        prompt_tokens = self.prompt_tokens

        total_tokens = self.total_tokens

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if completion_tokens is not UNSET:
            field_dict["completion_tokens"] = completion_tokens
        if prompt_tokens is not UNSET:
            field_dict["prompt_tokens"] = prompt_tokens
        if total_tokens is not UNSET:
            field_dict["total_tokens"] = total_tokens

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        completion_tokens = d.pop("completion_tokens", UNSET)

        prompt_tokens = d.pop("prompt_tokens", UNSET)

        total_tokens = d.pop("total_tokens", UNSET)

        chat_competion_usage = cls(
            completion_tokens=completion_tokens,
            prompt_tokens=prompt_tokens,
            total_tokens=total_tokens,
        )

        chat_competion_usage.additional_properties = d
        return chat_competion_usage

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
