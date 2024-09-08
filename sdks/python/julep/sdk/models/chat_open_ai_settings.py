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

T = TypeVar("T", bound="ChatOpenAISettings")


@_attrs_define
class ChatOpenAISettings:
    """
    Attributes:
        frequency_penalty (Union[Unset, float]): Number between -2.0 and 2.0. Positive values penalize new tokens based
            on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line
            verbatim.
        presence_penalty (Union[Unset, float]): Number between -2.0 and 2.0. Positive values penalize new tokens based
            on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line
            verbatim.
        temperature (Union[Unset, float]): What sampling temperature to use, between 0 and 2. Higher values like 0.8
            will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
        top_p (Union[Unset, float]): Defaults to 1 An alternative to sampling with temperature, called nucleus sampling,
            where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens
            comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but
            not both.
    """

    frequency_penalty: Union[Unset, float] = UNSET
    presence_penalty: Union[Unset, float] = UNSET
    temperature: Union[Unset, float] = UNSET
    top_p: Union[Unset, float] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        frequency_penalty = self.frequency_penalty

        presence_penalty = self.presence_penalty

        temperature = self.temperature

        top_p = self.top_p

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if frequency_penalty is not UNSET:
            field_dict["frequency_penalty"] = frequency_penalty
        if presence_penalty is not UNSET:
            field_dict["presence_penalty"] = presence_penalty
        if temperature is not UNSET:
            field_dict["temperature"] = temperature
        if top_p is not UNSET:
            field_dict["top_p"] = top_p

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        frequency_penalty = d.pop("frequency_penalty", UNSET)

        presence_penalty = d.pop("presence_penalty", UNSET)

        temperature = d.pop("temperature", UNSET)

        top_p = d.pop("top_p", UNSET)

        chat_open_ai_settings = cls(
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            temperature=temperature,
            top_p=top_p,
        )

        chat_open_ai_settings.additional_properties = d
        return chat_open_ai_settings

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
