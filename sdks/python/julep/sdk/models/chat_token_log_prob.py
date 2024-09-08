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
    from ..models.base_token_log_prob import BaseTokenLogProb


T = TypeVar("T", bound="ChatTokenLogProb")


@_attrs_define
class ChatTokenLogProb:
    """
    Attributes:
        token (str):
        logprob (float): The log probability of the token
        top_logprobs (List['BaseTokenLogProb']): The log probabilities of the tokens
        bytes_ (Union[Unset, List[int]]):
    """

    token: str
    logprob: float
    top_logprobs: List["BaseTokenLogProb"]
    bytes_: Union[Unset, List[int]] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.base_token_log_prob import BaseTokenLogProb

        token = self.token

        logprob = self.logprob

        top_logprobs = []
        for top_logprobs_item_data in self.top_logprobs:
            top_logprobs_item = top_logprobs_item_data.to_dict()
            top_logprobs.append(top_logprobs_item)

        bytes_: Union[Unset, List[int]] = UNSET
        if not isinstance(self.bytes_, Unset):
            bytes_ = self.bytes_

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "token": token,
                "logprob": logprob,
                "top_logprobs": top_logprobs,
            }
        )
        if bytes_ is not UNSET:
            field_dict["bytes"] = bytes_

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.base_token_log_prob import BaseTokenLogProb

        d = src_dict.copy()
        token = d.pop("token")

        logprob = d.pop("logprob")

        top_logprobs = []
        _top_logprobs = d.pop("top_logprobs")
        for top_logprobs_item_data in _top_logprobs:
            top_logprobs_item = BaseTokenLogProb.from_dict(top_logprobs_item_data)

            top_logprobs.append(top_logprobs_item)

        bytes_ = cast(List[int], d.pop("bytes", UNSET))

        chat_token_log_prob = cls(
            token=token,
            logprob=logprob,
            top_logprobs=top_logprobs,
            bytes_=bytes_,
        )

        chat_token_log_prob.additional_properties = d
        return chat_token_log_prob

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
