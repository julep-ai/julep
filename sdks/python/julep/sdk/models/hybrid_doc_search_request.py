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

from ..models.hybrid_doc_search_request_lang import HybridDocSearchRequestLang
from ..types import UNSET, Unset

T = TypeVar("T", bound="HybridDocSearchRequest")


@_attrs_define
class HybridDocSearchRequest:
    """
    Attributes:
        limit (int):  Default: 10.
        lang (HybridDocSearchRequestLang): The language to be used for text-only search. Support for other languages
            coming soon. Default: HybridDocSearchRequestLang.EN_US.
        confidence (float): The confidence cutoff level Default: 0.5.
        alpha (float): The weight to apply to BM25 vs Vector search results. 0 => pure BM25; 1 => pure vector; Default:
            0.75.
        text (str): Text to use in the search. In `hybrid` search mode, either `text` or both `text` and `vector` fields
            are required.
        vector (List[float]): Vector to use in the search. Must be the same dimensions as the embedding model or else an
            error will be thrown.
    """

    text: str
    vector: List[float]
    limit: int = 10
    lang: HybridDocSearchRequestLang = HybridDocSearchRequestLang.EN_US
    confidence: float = 0.5
    alpha: float = 0.75
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        limit = self.limit

        lang = self.lang.value

        confidence = self.confidence

        alpha = self.alpha

        text = self.text

        vector = self.vector

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "limit": limit,
                "lang": lang,
                "confidence": confidence,
                "alpha": alpha,
                "text": text,
                "vector": vector,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        limit = d.pop("limit")

        lang = HybridDocSearchRequestLang(d.pop("lang"))

        confidence = d.pop("confidence")

        alpha = d.pop("alpha")

        text = d.pop("text")

        vector = cast(List[float], d.pop("vector"))

        hybrid_doc_search_request = cls(
            limit=limit,
            lang=lang,
            confidence=confidence,
            alpha=alpha,
            text=text,
            vector=vector,
        )

        hybrid_doc_search_request.additional_properties = d
        return hybrid_doc_search_request

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
