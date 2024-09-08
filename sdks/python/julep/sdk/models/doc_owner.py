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

from ..models.doc_owner_role import DocOwnerRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="DocOwner")


@_attrs_define
class DocOwner:
    """
    Attributes:
        id (str):
        role (DocOwnerRole):
    """

    id: str
    role: DocOwnerRole
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id: str
        id = self.id

        role = self.role.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "role": role,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()

        def _parse_id(data: object) -> str:
            return cast(str, data)

        id = _parse_id(d.pop("id"))

        role = DocOwnerRole(d.pop("role"))

        doc_owner = cls(
            id=id,
            role=role,
        )

        doc_owner.additional_properties = d
        return doc_owner

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
