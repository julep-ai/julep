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
    from ..models.chat_competion_usage import ChatCompetionUsage
    from ..models.doc_reference import DocReference


T = TypeVar("T", bound="BaseChatResponse")


@_attrs_define
class BaseChatResponse:
    """
    Attributes:
        jobs (List[str]): Background job IDs that may have been spawned from this interaction.
        docs (List['DocReference']): Documents referenced for this request (for citation purposes).
        created_at (datetime.datetime): When this resource was created as UTC date-time
        id (str):
        usage (Union[Unset, ChatCompetionUsage]): Usage statistics for the completion request
    """

    jobs: List[str]
    docs: List["DocReference"]
    created_at: datetime.datetime
    id: str
    usage: Union[Unset, "ChatCompetionUsage"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.chat_competion_usage import ChatCompetionUsage
        from ..models.doc_reference import DocReference

        jobs = self.jobs

        docs = []
        for docs_item_data in self.docs:
            docs_item = docs_item_data.to_dict()
            docs.append(docs_item)

        created_at = self.created_at.isoformat()

        id = self.id

        usage: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.usage, Unset):
            usage = self.usage.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "jobs": jobs,
                "docs": docs,
                "created_at": created_at,
                "id": id,
            }
        )
        if usage is not UNSET:
            field_dict["usage"] = usage

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.chat_competion_usage import ChatCompetionUsage
        from ..models.doc_reference import DocReference

        d = src_dict.copy()
        jobs = cast(List[str], d.pop("jobs"))

        docs = []
        _docs = d.pop("docs")
        for docs_item_data in _docs:
            docs_item = DocReference.from_dict(docs_item_data)

            docs.append(docs_item)

        created_at = isoparse(d.pop("created_at"))

        id = d.pop("id")

        _usage = d.pop("usage", UNSET)
        usage: Union[Unset, ChatCompetionUsage]
        if isinstance(_usage, Unset):
            usage = UNSET
        else:
            usage = ChatCompetionUsage.from_dict(_usage)

        base_chat_response = cls(
            jobs=jobs,
            docs=docs,
            created_at=created_at,
            id=id,
            usage=usage,
        )

        base_chat_response.additional_properties = d
        return base_chat_response

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
