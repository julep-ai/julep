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

from ..models.chat_finish_reason import ChatFinishReason
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_log_prob_response import ChatLogProbResponse


T = TypeVar("T", bound="BaseChatOutput")


@_attrs_define
class BaseChatOutput:
    """
    Attributes:
        index (int):
        finish_reason (ChatFinishReason): The reason the model stopped generating tokens. This will be `stop`
            if the model hit a natural stop point or a provided stop sequence,
            `length` if the maximum number of tokens specified in the request
            was reached, `content_filter` if content was omitted due to a flag
            from our content filters, `tool_calls` if the model called a tool. Default: ChatFinishReason.STOP.
        logprobs (Union[Unset, ChatLogProbResponse]):
    """

    index: int
    finish_reason: ChatFinishReason = ChatFinishReason.STOP
    logprobs: Union[Unset, "ChatLogProbResponse"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.chat_log_prob_response import ChatLogProbResponse

        index = self.index

        finish_reason = self.finish_reason.value

        logprobs: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.logprobs, Unset):
            logprobs = self.logprobs.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "index": index,
                "finish_reason": finish_reason,
            }
        )
        if logprobs is not UNSET:
            field_dict["logprobs"] = logprobs

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.chat_log_prob_response import ChatLogProbResponse

        d = src_dict.copy()
        index = d.pop("index")

        finish_reason = ChatFinishReason(d.pop("finish_reason"))

        _logprobs = d.pop("logprobs", UNSET)
        logprobs: Union[Unset, ChatLogProbResponse]
        if isinstance(_logprobs, Unset):
            logprobs = UNSET
        else:
            logprobs = ChatLogProbResponse.from_dict(_logprobs)

        base_chat_output = cls(
            index=index,
            finish_reason=finish_reason,
            logprobs=logprobs,
        )

        base_chat_output.additional_properties = d
        return base_chat_output

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
