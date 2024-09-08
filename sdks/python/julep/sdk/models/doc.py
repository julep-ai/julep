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
    from ..models.doc_metadata import DocMetadata


T = TypeVar("T", bound="Doc")


@_attrs_define
class Doc:
    """
    Attributes:
        id (str):
        created_at (datetime.datetime): When this resource was created as UTC date-time
        title (str): Title describing what this document contains
        content (Union[List[str], str]): Contents of the document
        metadata (Union[Unset, DocMetadata]):
    """

    id: str
    created_at: datetime.datetime
    title: str
    content: Union[List[str], str]
    metadata: Union[Unset, "DocMetadata"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.doc_metadata import DocMetadata

        id = self.id

        created_at = self.created_at.isoformat()

        title = self.title

        content: Union[List[str], str]
        if isinstance(self.content, list):
            content = self.content

        else:
            content = self.content

        metadata: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "created_at": created_at,
                "title": title,
                "content": content,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.doc_metadata import DocMetadata

        d = src_dict.copy()
        id = d.pop("id")

        created_at = isoparse(d.pop("created_at"))

        title = d.pop("title")

        def _parse_content(data: object) -> Union[List[str], str]:
            try:
                if not isinstance(data, list):
                    raise TypeError()
                content_type_1 = cast(List[str], data)

                return content_type_1
            except:  # noqa: E722
                pass
            return cast(Union[List[str], str], data)

        content = _parse_content(d.pop("content"))

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, DocMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = DocMetadata.from_dict(_metadata)

        doc = cls(
            id=id,
            created_at=created_at,
            title=title,
            content=content,
            metadata=metadata,
        )

        doc.additional_properties = d
        return doc

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
