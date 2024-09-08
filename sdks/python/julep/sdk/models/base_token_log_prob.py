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

T = TypeVar("T", bound="BaseTokenLogProb")


@_attrs_define
class BaseTokenLogProb:
    """
    Attributes:
        token (str):
        logprob (float): The log probability of the token
        bytes_ (Union[Unset, List[int]]):
    """

    token: str
    logprob: float
    bytes_: Union[Unset, List[int]] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        token = self.token

        logprob = self.logprob

        bytes_: Union[Unset, List[int]] = UNSET
        if not isinstance(self.bytes_, Unset):
            bytes_ = self.bytes_

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "token": token,
                "logprob": logprob,
            }
        )
        if bytes_ is not UNSET:
            field_dict["bytes"] = bytes_

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        token = d.pop("token")

        logprob = d.pop("logprob")

        bytes_ = cast(List[int], d.pop("bytes", UNSET))

        base_token_log_prob = cls(
            token=token,
            logprob=logprob,
            bytes_=bytes_,
        )

        base_token_log_prob.additional_properties = d
        return base_token_log_prob

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
