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
    from ..models.patch_user_request_metadata import PatchUserRequestMetadata


T = TypeVar("T", bound="PatchUserRequest")


@_attrs_define
class PatchUserRequest:
    """Payload for patching a user

    Attributes:
        metadata (Union[Unset, PatchUserRequestMetadata]):
        name (Union[Unset, str]): For Unicode character safety
            See: https://unicode.org/reports/tr31/
            See: https://www.unicode.org/reports/tr39/#Identifier_Characters Default: ''.
        about (Union[Unset, str]): About the user Default: ''.
    """

    metadata: Union[Unset, "PatchUserRequestMetadata"] = UNSET
    name: Union[Unset, str] = ""
    about: Union[Unset, str] = ""
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.patch_user_request_metadata import PatchUserRequestMetadata

        metadata: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        name = self.name

        about = self.about

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if name is not UNSET:
            field_dict["name"] = name
        if about is not UNSET:
            field_dict["about"] = about

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.patch_user_request_metadata import PatchUserRequestMetadata

        d = src_dict.copy()
        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, PatchUserRequestMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = PatchUserRequestMetadata.from_dict(_metadata)

        name = d.pop("name", UNSET)

        about = d.pop("about", UNSET)

        patch_user_request = cls(
            metadata=metadata,
            name=name,
            about=about,
        )

        patch_user_request.additional_properties = d
        return patch_user_request

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
