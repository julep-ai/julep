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

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.doc_reference import DocReference


T = TypeVar("T", bound="DocSearchResponse")


@_attrs_define
class DocSearchResponse:
    """
    Attributes:
        docs (List['DocReference']): The documents that were found
        time (float): The time taken to search in seconds
    """

    docs: List["DocReference"]
    time: float
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.doc_reference import DocReference

        docs = []
        for docs_item_data in self.docs:
            docs_item = docs_item_data.to_dict()
            docs.append(docs_item)

        time = self.time

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "docs": docs,
                "time": time,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.doc_reference import DocReference

        d = src_dict.copy()
        docs = []
        _docs = d.pop("docs")
        for docs_item_data in _docs:
            docs_item = DocReference.from_dict(docs_item_data)

            docs.append(docs_item)

        time = d.pop("time")

        doc_search_response = cls(
            docs=docs,
            time=time,
        )

        doc_search_response.additional_properties = d
        return doc_search_response

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
