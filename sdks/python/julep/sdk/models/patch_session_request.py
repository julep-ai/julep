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

from ..models.context_overflow_type import ContextOverflowType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.patch_session_request_metadata import PatchSessionRequestMetadata


T = TypeVar("T", bound="PatchSessionRequest")


@_attrs_define
class PatchSessionRequest:
    r"""Payload for patching a session

    Attributes:
        situation (Union[Unset, str]): A specific situation that sets the background for this session Default: '{%- if
            agent.name -%}\nYou are {{agent.name}}.{{\\" \\"}}\n{%- endif -%}\n\n{%- if agent.about -%}\nAbout you:
            {{agent.name}}.{{\\" \\"}}\n{%- endif -%}\n\n{%- if user -%}\nYou are talking to a user\n  {%- if user.name
            -%}{{\\" \\"}} and their name is {{user.name}}\n    {%- if user.about -%}. About the user: {{user.about}}.{%-
            else -%}.{%- endif -%}\n  {%- endif -%}\n{%- endif -%}\n\n{{\\"\n\n\\"}}\n\n{%- if agent.instructions
            -%}\nInstructions:{{\\"\n\\"}}\n  {%- if agent.instructions is string -%}\n
            {{agent.instructions}}{{\\"\n\\"}}\n  {%- else -%}\n    {%- for instruction in agent.instructions -%}\n      -
            {{instruction}}{{\\"\n\\"}}\n    {%- endfor -%}\n  {%- endif -%}\n  {{\\"\n\\"}}\n{%- endif -%}\n\n{%- if tools
            -%}\nTools:{{\\"\n\\"}}\n  {%- for tool in tools -%}\n    {%- if tool.type == \\"function\\" -%}\n      -
            {{tool.function.name}}\n      {%- if tool.function.description -%}: {{tool.function.description}}{%- endif
            -%}{{\\"\n\\"}}\n    {%- else -%}\n      - {{ 0/0 }} {# Error: Other tool types aren\'t supported yet. #}\n
            {%- endif -%}\n  {%- endfor -%}\n{{\\"\n\n\\"}}\n{%- endif -%}\n\n{%- if docs -%}\nRelevant
            documents:{{\\"\n\\"}}\n  {%- for doc in docs -%}\n    {{doc.title}}{{\\"\n\\"}}\n    {%- if doc.content is
            string -%}\n      {{doc.content}}{{\\"\n\\"}}\n    {%- else -%}\n      {%- for snippet in doc.content -%}\n
            {{snippet}}{{\\"\n\\"}}\n      {%- endfor -%}\n    {%- endif -%}\n    {{\\"---\\"}}\n  {%- endfor -%}\n{%- endif
            -%}'.
        render_templates (Union[Unset, bool]): Render system and assistant message content as jinja templates Default:
            True.
        token_budget (Union[None, Unset, int]): Threshold value for the adaptive context functionality
        context_overflow (Union[ContextOverflowType, None, Unset]): Action to start on context window overflow
        metadata (Union[Unset, PatchSessionRequestMetadata]):
    """

    situation: Union[Unset, str] = (
        '{%- if agent.name -%}\nYou are {{agent.name}}.{{\\" \\"}}\n{%- endif -%}\n\n{%- if agent.about -%}\nAbout you: {{agent.name}}.{{\\" \\"}}\n{%- endif -%}\n\n{%- if user -%}\nYou are talking to a user\n  {%- if user.name -%}{{\\" \\"}} and their name is {{user.name}}\n    {%- if user.about -%}. About the user: {{user.about}}.{%- else -%}.{%- endif -%}\n  {%- endif -%}\n{%- endif -%}\n\n{{\\"\n\n\\"}}\n\n{%- if agent.instructions -%}\nInstructions:{{\\"\n\\"}}\n  {%- if agent.instructions is string -%}\n    {{agent.instructions}}{{\\"\n\\"}}\n  {%- else -%}\n    {%- for instruction in agent.instructions -%}\n      - {{instruction}}{{\\"\n\\"}}\n    {%- endfor -%}\n  {%- endif -%}\n  {{\\"\n\\"}}\n{%- endif -%}\n\n{%- if tools -%}\nTools:{{\\"\n\\"}}\n  {%- for tool in tools -%}\n    {%- if tool.type == \\"function\\" -%}\n      - {{tool.function.name}}\n      {%- if tool.function.description -%}: {{tool.function.description}}{%- endif -%}{{\\"\n\\"}}\n    {%- else -%}\n      - {{ 0/0 }} {# Error: Other tool types aren\'t supported yet. #}\n    {%- endif -%}\n  {%- endfor -%}\n{{\\"\n\n\\"}}\n{%- endif -%}\n\n{%- if docs -%}\nRelevant documents:{{\\"\n\\"}}\n  {%- for doc in docs -%}\n    {{doc.title}}{{\\"\n\\"}}\n    {%- if doc.content is string -%}\n      {{doc.content}}{{\\"\n\\"}}\n    {%- else -%}\n      {%- for snippet in doc.content -%}\n        {{snippet}}{{\\"\n\\"}}\n      {%- endfor -%}\n    {%- endif -%}\n    {{\\"---\\"}}\n  {%- endfor -%}\n{%- endif -%}'
    )
    render_templates: Union[Unset, bool] = True
    token_budget: Union[None, Unset, int] = UNSET
    context_overflow: Union[ContextOverflowType, None, Unset] = UNSET
    metadata: Union[Unset, "PatchSessionRequestMetadata"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.patch_session_request_metadata import PatchSessionRequestMetadata

        situation = self.situation

        render_templates = self.render_templates

        token_budget: Union[None, Unset, int]
        if isinstance(self.token_budget, Unset):
            token_budget = UNSET
        else:
            token_budget = self.token_budget

        context_overflow: Union[None, Unset, str]
        if isinstance(self.context_overflow, Unset):
            context_overflow = UNSET
        elif isinstance(self.context_overflow, ContextOverflowType):
            context_overflow = self.context_overflow.value
        else:
            context_overflow = self.context_overflow

        metadata: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if situation is not UNSET:
            field_dict["situation"] = situation
        if render_templates is not UNSET:
            field_dict["render_templates"] = render_templates
        if token_budget is not UNSET:
            field_dict["token_budget"] = token_budget
        if context_overflow is not UNSET:
            field_dict["context_overflow"] = context_overflow
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.patch_session_request_metadata import PatchSessionRequestMetadata

        d = src_dict.copy()
        situation = d.pop("situation", UNSET)

        render_templates = d.pop("render_templates", UNSET)

        def _parse_token_budget(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        token_budget = _parse_token_budget(d.pop("token_budget", UNSET))

        def _parse_context_overflow(
            data: object,
        ) -> Union[ContextOverflowType, None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                context_overflow_type_0 = ContextOverflowType(data)

                return context_overflow_type_0
            except:  # noqa: E722
                pass
            return cast(Union[ContextOverflowType, None, Unset], data)

        context_overflow = _parse_context_overflow(d.pop("context_overflow", UNSET))

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, PatchSessionRequestMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = PatchSessionRequestMetadata.from_dict(_metadata)

        patch_session_request = cls(
            situation=situation,
            render_templates=render_templates,
            token_budget=token_budget,
            context_overflow=context_overflow,
            metadata=metadata,
        )

        patch_session_request.additional_properties = d
        return patch_session_request

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
