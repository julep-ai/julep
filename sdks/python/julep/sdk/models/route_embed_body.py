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
    from ..models.embed_query_request import EmbedQueryRequest


T = TypeVar("T", bound="RouteEmbedBody")


@_attrs_define
class RouteEmbedBody:
    """
    Attributes:
        body (EmbedQueryRequest):
    """

    body: "EmbedQueryRequest"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.embed_query_request import EmbedQueryRequest

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
        from ..models.embed_query_request import EmbedQueryRequest

        d = src_dict.copy()
        body = EmbedQueryRequest.from_dict(d.pop("body"))

        route_embed_body = cls(
            body=body,
        )

        route_embed_body.additional_properties = d
        return route_embed_body

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
