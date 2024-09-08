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
    from ..models.update_user_request_metadata import UpdateUserRequestMetadata


T = TypeVar("T", bound="UpdateUserRequest")


@_attrs_define
class UpdateUserRequest:
    """Payload for updating a user

    Attributes:
        name (str): For Unicode character safety
            See: https://unicode.org/reports/tr31/
            See: https://www.unicode.org/reports/tr39/#Identifier_Characters Default: ''.
        about (str): About the user Default: ''.
        metadata (Union[Unset, UpdateUserRequestMetadata]):
    """

    name: str = ""
    about: str = ""
    metadata: Union[Unset, "UpdateUserRequestMetadata"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.update_user_request_metadata import UpdateUserRequestMetadata

        name = self.name

        about = self.about

        metadata: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "about": about,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.update_user_request_metadata import UpdateUserRequestMetadata

        d = src_dict.copy()
        name = d.pop("name")

        about = d.pop("about")

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, UpdateUserRequestMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = UpdateUserRequestMetadata.from_dict(_metadata)

        update_user_request = cls(
            name=name,
            about=about,
            metadata=metadata,
        )

        update_user_request.additional_properties = d
        return update_user_request

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
