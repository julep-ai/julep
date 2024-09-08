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

from ..models.base_doc_search_request_lang import BaseDocSearchRequestLang
from ..types import UNSET, Unset

T = TypeVar("T", bound="BaseDocSearchRequest")


@_attrs_define
class BaseDocSearchRequest:
    """
    Attributes:
        limit (int):  Default: 10.
        lang (BaseDocSearchRequestLang): The language to be used for text-only search. Support for other languages
            coming soon. Default: BaseDocSearchRequestLang.EN_US.
    """

    limit: int = 10
    lang: BaseDocSearchRequestLang = BaseDocSearchRequestLang.EN_US
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        limit = self.limit

        lang = self.lang.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "limit": limit,
                "lang": lang,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        limit = d.pop("limit")

        lang = BaseDocSearchRequestLang(d.pop("lang"))

        base_doc_search_request = cls(
            limit=limit,
            lang=lang,
        )

        base_doc_search_request.additional_properties = d
        return base_doc_search_request

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
