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

from ..models.search_step_kind import SearchStepKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.base_doc_search_request import BaseDocSearchRequest


T = TypeVar("T", bound="SearchStep")


@_attrs_define
class SearchStep:
    """
    Attributes:
        kind (SearchStepKind): The kind of step
        search ('BaseDocSearchRequest'): The search query
    """

    kind: SearchStepKind
    search: "BaseDocSearchRequest"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.base_doc_search_request import BaseDocSearchRequest

        kind = self.kind.value

        search: Dict[str, Any]
        if isinstance(self.search, BaseDocSearchRequest):
            search = self.search.to_dict()
        elif isinstance(self.search, BaseDocSearchRequest):
            search = self.search.to_dict()
        else:
            search = self.search.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind_": kind,
                "search": search,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.base_doc_search_request import BaseDocSearchRequest

        d = src_dict.copy()
        kind = SearchStepKind(d.pop("kind_"))

        def _parse_search(data: object) -> "BaseDocSearchRequest":
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                search_type_0 = BaseDocSearchRequest.from_dict(data)

                return search_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                search_type_1 = BaseDocSearchRequest.from_dict(data)

                return search_type_1
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            search_type_2 = BaseDocSearchRequest.from_dict(data)

            return search_type_2

        search = _parse_search(d.pop("search"))

        search_step = cls(
            kind=kind,
            search=search,
        )

        search_step.additional_properties = d
        return search_step

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
