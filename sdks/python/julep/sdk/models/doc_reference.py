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
    from ..models.doc_owner import DocOwner
    from ..models.snippet import Snippet


T = TypeVar("T", bound="DocReference")


@_attrs_define
class DocReference:
    """
    Attributes:
        owner (DocOwner):
        id (str):
        snippets (List['Snippet']):
        distance (Union[None, float]):
        title (Union[Unset, str]):
    """

    owner: "DocOwner"
    id: str
    snippets: List["Snippet"]
    distance: Union[None, float]
    title: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.doc_owner import DocOwner
        from ..models.snippet import Snippet

        owner = self.owner.to_dict()

        id = self.id

        snippets = []
        for snippets_item_data in self.snippets:
            snippets_item = snippets_item_data.to_dict()
            snippets.append(snippets_item)

        distance: Union[None, float]
        distance = self.distance

        title = self.title

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "owner": owner,
                "id": id,
                "snippets": snippets,
                "distance": distance,
            }
        )
        if title is not UNSET:
            field_dict["title"] = title

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.doc_owner import DocOwner
        from ..models.snippet import Snippet

        d = src_dict.copy()
        owner = DocOwner.from_dict(d.pop("owner"))

        id = d.pop("id")

        snippets = []
        _snippets = d.pop("snippets")
        for snippets_item_data in _snippets:
            snippets_item = Snippet.from_dict(snippets_item_data)

            snippets.append(snippets_item)

        def _parse_distance(data: object) -> Union[None, float]:
            if data is None:
                return data
            return cast(Union[None, float], data)

        distance = _parse_distance(d.pop("distance"))

        title = d.pop("title", UNSET)

        doc_reference = cls(
            owner=owner,
            id=id,
            snippets=snippets,
            distance=distance,
            title=title,
        )

        doc_reference.additional_properties = d
        return doc_reference

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
