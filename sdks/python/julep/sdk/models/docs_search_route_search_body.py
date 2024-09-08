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
    from ..models.hybrid_doc_search_request import HybridDocSearchRequest
    from ..models.text_only_doc_search_request import TextOnlyDocSearchRequest
    from ..models.vector_doc_search_request import VectorDocSearchRequest


T = TypeVar("T", bound="DocsSearchRouteSearchBody")


@_attrs_define
class DocsSearchRouteSearchBody:
    """
    Attributes:
        body (Union['HybridDocSearchRequest', 'TextOnlyDocSearchRequest', 'VectorDocSearchRequest']):
    """

    body: Union[
        "HybridDocSearchRequest", "TextOnlyDocSearchRequest", "VectorDocSearchRequest"
    ]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.hybrid_doc_search_request import HybridDocSearchRequest
        from ..models.text_only_doc_search_request import TextOnlyDocSearchRequest
        from ..models.vector_doc_search_request import VectorDocSearchRequest

        body: Dict[str, Any]
        if isinstance(self.body, VectorDocSearchRequest):
            body = self.body.to_dict()
        elif isinstance(self.body, TextOnlyDocSearchRequest):
            body = self.body.to_dict()
        else:
            body = self.body.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "body": body,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.hybrid_doc_search_request import HybridDocSearchRequest
        from ..models.text_only_doc_search_request import TextOnlyDocSearchRequest
        from ..models.vector_doc_search_request import VectorDocSearchRequest

        d = src_dict.copy()

        def _parse_body(
            data: object,
        ) -> Union[
            "HybridDocSearchRequest",
            "TextOnlyDocSearchRequest",
            "VectorDocSearchRequest",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                body_type_0 = VectorDocSearchRequest.from_dict(data)

                return body_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                body_type_1 = TextOnlyDocSearchRequest.from_dict(data)

                return body_type_1
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            body_type_2 = HybridDocSearchRequest.from_dict(data)

            return body_type_2

        body = _parse_body(d.pop("body"))

        docs_search_route_search_body = cls(
            body=body,
        )

        docs_search_route_search_body.additional_properties = d
        return docs_search_route_search_body

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
