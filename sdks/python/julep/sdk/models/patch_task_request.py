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
    from ..models.create_tool_request import CreateToolRequest
    from ..models.embed_step import EmbedStep
    from ..models.error_workflow_step import ErrorWorkflowStep
    from ..models.evaluate_step import EvaluateStep
    from ..models.foreach_step import ForeachStep
    from ..models.get_step import GetStep
    from ..models.if_else_workflow_step import IfElseWorkflowStep
    from ..models.log_step import LogStep
    from ..models.parallel_step import ParallelStep
    from ..models.patch_task_request_additional_property_item_type_17 import (
        PatchTaskRequestAdditionalPropertyItemType17,
    )
    from ..models.patch_task_request_input_schema_type_0 import (
        PatchTaskRequestInputSchemaType0,
    )
    from ..models.patch_task_request_main_item_type_17 import (
        PatchTaskRequestMainItemType17,
    )
    from ..models.patch_task_request_metadata import PatchTaskRequestMetadata
    from ..models.prompt_step import PromptStep
    from ..models.return_step import ReturnStep
    from ..models.search_step import SearchStep
    from ..models.set_step import SetStep
    from ..models.sleep_step import SleepStep
    from ..models.switch_step import SwitchStep
    from ..models.tool_call_step import ToolCallStep
    from ..models.wait_for_input_step import WaitForInputStep
    from ..models.yield_step import YieldStep


T = TypeVar("T", bound="PatchTaskRequest")


@_attrs_define
class PatchTaskRequest:
    """Payload for patching a task

    Attributes:
        description (Union[Unset, str]):  Default: ''.
        main (Union[Unset, List[Union['EmbedStep', 'ErrorWorkflowStep', 'EvaluateStep', 'ForeachStep', 'GetStep',
            'IfElseWorkflowStep', 'LogStep', 'ParallelStep', 'PatchTaskRequestMainItemType17', 'PromptStep', 'ReturnStep',
            'SearchStep', 'SetStep', 'SleepStep', 'SwitchStep', 'ToolCallStep', 'WaitForInputStep', 'YieldStep']]]): The
            entrypoint of the task.
        input_schema (Union['PatchTaskRequestInputSchemaType0', None, Unset]): The schema for the input to the task.
            `null` means all inputs are valid.
        tools (Union[Unset, List['CreateToolRequest']]): Tools defined specifically for this task not included in the
            Agent itself.
        inherit_tools (Union[Unset, bool]): Whether to inherit tools from the parent agent or not. Defaults to true.
            Default: True.
        metadata (Union[Unset, PatchTaskRequestMetadata]):
    """

    description: Union[Unset, str] = ""
    main: Union[
        Unset,
        List[
            Union[
                "EmbedStep",
                "ErrorWorkflowStep",
                "EvaluateStep",
                "ForeachStep",
                "GetStep",
                "IfElseWorkflowStep",
                "LogStep",
                "ParallelStep",
                "PatchTaskRequestMainItemType17",
                "PromptStep",
                "ReturnStep",
                "SearchStep",
                "SetStep",
                "SleepStep",
                "SwitchStep",
                "ToolCallStep",
                "WaitForInputStep",
                "YieldStep",
            ]
        ],
    ] = UNSET
    input_schema: Union["PatchTaskRequestInputSchemaType0", None, Unset] = UNSET
    tools: Union[Unset, List["CreateToolRequest"]] = UNSET
    inherit_tools: Union[Unset, bool] = True
    metadata: Union[Unset, "PatchTaskRequestMetadata"] = UNSET
    additional_properties: Dict[
        str,
        List[
            Union[
                "EmbedStep",
                "ErrorWorkflowStep",
                "EvaluateStep",
                "ForeachStep",
                "GetStep",
                "IfElseWorkflowStep",
                "LogStep",
                "ParallelStep",
                "PatchTaskRequestAdditionalPropertyItemType17",
                "PromptStep",
                "ReturnStep",
                "SearchStep",
                "SetStep",
                "SleepStep",
                "SwitchStep",
                "ToolCallStep",
                "WaitForInputStep",
                "YieldStep",
            ]
        ],
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.create_tool_request import CreateToolRequest
        from ..models.embed_step import EmbedStep
        from ..models.error_workflow_step import ErrorWorkflowStep
        from ..models.evaluate_step import EvaluateStep
        from ..models.foreach_step import ForeachStep
        from ..models.get_step import GetStep
        from ..models.if_else_workflow_step import IfElseWorkflowStep
        from ..models.log_step import LogStep
        from ..models.parallel_step import ParallelStep
        from ..models.patch_task_request_additional_property_item_type_17 import (
            PatchTaskRequestAdditionalPropertyItemType17,
        )
        from ..models.patch_task_request_input_schema_type_0 import (
            PatchTaskRequestInputSchemaType0,
        )
        from ..models.patch_task_request_main_item_type_17 import (
            PatchTaskRequestMainItemType17,
        )
        from ..models.patch_task_request_metadata import PatchTaskRequestMetadata
        from ..models.prompt_step import PromptStep
        from ..models.return_step import ReturnStep
        from ..models.search_step import SearchStep
        from ..models.set_step import SetStep
        from ..models.sleep_step import SleepStep
        from ..models.switch_step import SwitchStep
        from ..models.tool_call_step import ToolCallStep
        from ..models.wait_for_input_step import WaitForInputStep
        from ..models.yield_step import YieldStep

        description = self.description

        main: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.main, Unset):
            main = []
            for main_item_data in self.main:
                main_item: Dict[str, Any]
                if isinstance(main_item_data, EvaluateStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, ToolCallStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, PromptStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, GetStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, SetStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, LogStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, EmbedStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, SearchStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, ReturnStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, SleepStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, ErrorWorkflowStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, YieldStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, WaitForInputStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, IfElseWorkflowStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, SwitchStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, ForeachStep):
                    main_item = main_item_data.to_dict()
                elif isinstance(main_item_data, ParallelStep):
                    main_item = main_item_data.to_dict()
                else:
                    main_item = main_item_data.to_dict()

                main.append(main_item)

        input_schema: Union[Dict[str, Any], None, Unset]
        if isinstance(self.input_schema, Unset):
            input_schema = UNSET
        elif isinstance(self.input_schema, PatchTaskRequestInputSchemaType0):
            input_schema = self.input_schema.to_dict()
        else:
            input_schema = self.input_schema

        tools: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.tools, Unset):
            tools = []
            for tools_item_data in self.tools:
                tools_item = tools_item_data.to_dict()
                tools.append(tools_item)

        inherit_tools = self.inherit_tools

        metadata: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: Dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = []
            for additional_property_item_data in prop:
                additional_property_item: Dict[str, Any]
                if isinstance(additional_property_item_data, EvaluateStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, ToolCallStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, PromptStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, GetStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, SetStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, LogStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, EmbedStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, SearchStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, ReturnStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, SleepStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, ErrorWorkflowStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, YieldStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, WaitForInputStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, IfElseWorkflowStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, SwitchStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, ForeachStep):
                    additional_property_item = additional_property_item_data.to_dict()
                elif isinstance(additional_property_item_data, ParallelStep):
                    additional_property_item = additional_property_item_data.to_dict()
                else:
                    additional_property_item = additional_property_item_data.to_dict()

                field_dict[prop_name].append(additional_property_item)

        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if main is not UNSET:
            field_dict["main"] = main
        if input_schema is not UNSET:
            field_dict["input_schema"] = input_schema
        if tools is not UNSET:
            field_dict["tools"] = tools
        if inherit_tools is not UNSET:
            field_dict["inherit_tools"] = inherit_tools
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.create_tool_request import CreateToolRequest
        from ..models.embed_step import EmbedStep
        from ..models.error_workflow_step import ErrorWorkflowStep
        from ..models.evaluate_step import EvaluateStep
        from ..models.foreach_step import ForeachStep
        from ..models.get_step import GetStep
        from ..models.if_else_workflow_step import IfElseWorkflowStep
        from ..models.log_step import LogStep
        from ..models.parallel_step import ParallelStep
        from ..models.patch_task_request_additional_property_item_type_17 import (
            PatchTaskRequestAdditionalPropertyItemType17,
        )
        from ..models.patch_task_request_input_schema_type_0 import (
            PatchTaskRequestInputSchemaType0,
        )
        from ..models.patch_task_request_main_item_type_17 import (
            PatchTaskRequestMainItemType17,
        )
        from ..models.patch_task_request_metadata import PatchTaskRequestMetadata
        from ..models.prompt_step import PromptStep
        from ..models.return_step import ReturnStep
        from ..models.search_step import SearchStep
        from ..models.set_step import SetStep
        from ..models.sleep_step import SleepStep
        from ..models.switch_step import SwitchStep
        from ..models.tool_call_step import ToolCallStep
        from ..models.wait_for_input_step import WaitForInputStep
        from ..models.yield_step import YieldStep

        d = src_dict.copy()
        description = d.pop("description", UNSET)

        main = []
        _main = d.pop("main", UNSET)
        for main_item_data in _main or []:

            def _parse_main_item(
                data: object,
            ) -> Union[
                "EmbedStep",
                "ErrorWorkflowStep",
                "EvaluateStep",
                "ForeachStep",
                "GetStep",
                "IfElseWorkflowStep",
                "LogStep",
                "ParallelStep",
                "PatchTaskRequestMainItemType17",
                "PromptStep",
                "ReturnStep",
                "SearchStep",
                "SetStep",
                "SleepStep",
                "SwitchStep",
                "ToolCallStep",
                "WaitForInputStep",
                "YieldStep",
            ]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_0 = EvaluateStep.from_dict(data)

                    return main_item_type_0
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_1 = ToolCallStep.from_dict(data)

                    return main_item_type_1
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_2 = PromptStep.from_dict(data)

                    return main_item_type_2
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_3 = GetStep.from_dict(data)

                    return main_item_type_3
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_4 = SetStep.from_dict(data)

                    return main_item_type_4
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_5 = LogStep.from_dict(data)

                    return main_item_type_5
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_6 = EmbedStep.from_dict(data)

                    return main_item_type_6
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_7 = SearchStep.from_dict(data)

                    return main_item_type_7
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_8 = ReturnStep.from_dict(data)

                    return main_item_type_8
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_9 = SleepStep.from_dict(data)

                    return main_item_type_9
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_10 = ErrorWorkflowStep.from_dict(data)

                    return main_item_type_10
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_11 = YieldStep.from_dict(data)

                    return main_item_type_11
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_12 = WaitForInputStep.from_dict(data)

                    return main_item_type_12
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_13 = IfElseWorkflowStep.from_dict(data)

                    return main_item_type_13
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_14 = SwitchStep.from_dict(data)

                    return main_item_type_14
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_15 = ForeachStep.from_dict(data)

                    return main_item_type_15
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    main_item_type_16 = ParallelStep.from_dict(data)

                    return main_item_type_16
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                main_item_type_17 = PatchTaskRequestMainItemType17.from_dict(data)

                return main_item_type_17

            main_item = _parse_main_item(main_item_data)

            main.append(main_item)

        def _parse_input_schema(
            data: object,
        ) -> Union["PatchTaskRequestInputSchemaType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                input_schema_type_0 = PatchTaskRequestInputSchemaType0.from_dict(data)

                return input_schema_type_0
            except:  # noqa: E722
                pass
            return cast(Union["PatchTaskRequestInputSchemaType0", None, Unset], data)

        input_schema = _parse_input_schema(d.pop("input_schema", UNSET))

        tools = []
        _tools = d.pop("tools", UNSET)
        for tools_item_data in _tools or []:
            tools_item = CreateToolRequest.from_dict(tools_item_data)

            tools.append(tools_item)

        inherit_tools = d.pop("inherit_tools", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, PatchTaskRequestMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = PatchTaskRequestMetadata.from_dict(_metadata)

        patch_task_request = cls(
            description=description,
            main=main,
            input_schema=input_schema,
            tools=tools,
            inherit_tools=inherit_tools,
            metadata=metadata,
        )

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = []
            _additional_property = prop_dict
            for additional_property_item_data in _additional_property:

                def _parse_additional_property_item(
                    data: object,
                ) -> Union[
                    "EmbedStep",
                    "ErrorWorkflowStep",
                    "EvaluateStep",
                    "ForeachStep",
                    "GetStep",
                    "IfElseWorkflowStep",
                    "LogStep",
                    "ParallelStep",
                    "PatchTaskRequestAdditionalPropertyItemType17",
                    "PromptStep",
                    "ReturnStep",
                    "SearchStep",
                    "SetStep",
                    "SleepStep",
                    "SwitchStep",
                    "ToolCallStep",
                    "WaitForInputStep",
                    "YieldStep",
                ]:
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_0 = EvaluateStep.from_dict(data)

                        return additional_property_item_type_0
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_1 = ToolCallStep.from_dict(data)

                        return additional_property_item_type_1
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_2 = PromptStep.from_dict(data)

                        return additional_property_item_type_2
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_3 = GetStep.from_dict(data)

                        return additional_property_item_type_3
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_4 = SetStep.from_dict(data)

                        return additional_property_item_type_4
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_5 = LogStep.from_dict(data)

                        return additional_property_item_type_5
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_6 = EmbedStep.from_dict(data)

                        return additional_property_item_type_6
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_7 = SearchStep.from_dict(data)

                        return additional_property_item_type_7
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_8 = ReturnStep.from_dict(data)

                        return additional_property_item_type_8
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_9 = SleepStep.from_dict(data)

                        return additional_property_item_type_9
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_10 = ErrorWorkflowStep.from_dict(
                            data
                        )

                        return additional_property_item_type_10
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_11 = YieldStep.from_dict(data)

                        return additional_property_item_type_11
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_12 = WaitForInputStep.from_dict(
                            data
                        )

                        return additional_property_item_type_12
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_13 = IfElseWorkflowStep.from_dict(
                            data
                        )

                        return additional_property_item_type_13
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_14 = SwitchStep.from_dict(data)

                        return additional_property_item_type_14
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_15 = ForeachStep.from_dict(data)

                        return additional_property_item_type_15
                    except:  # noqa: E722
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        additional_property_item_type_16 = ParallelStep.from_dict(data)

                        return additional_property_item_type_16
                    except:  # noqa: E722
                        pass
                    if not isinstance(data, dict):
                        raise TypeError()
                    additional_property_item_type_17 = (
                        PatchTaskRequestAdditionalPropertyItemType17.from_dict(data)
                    )

                    return additional_property_item_type_17

                additional_property_item = _parse_additional_property_item(
                    additional_property_item_data
                )

                additional_property.append(additional_property_item)

            additional_properties[prop_name] = additional_property

        patch_task_request.additional_properties = additional_properties
        return patch_task_request

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(
        self, key: str
    ) -> List[
        Union[
            "EmbedStep",
            "ErrorWorkflowStep",
            "EvaluateStep",
            "ForeachStep",
            "GetStep",
            "IfElseWorkflowStep",
            "LogStep",
            "ParallelStep",
            "PatchTaskRequestAdditionalPropertyItemType17",
            "PromptStep",
            "ReturnStep",
            "SearchStep",
            "SetStep",
            "SleepStep",
            "SwitchStep",
            "ToolCallStep",
            "WaitForInputStep",
            "YieldStep",
        ]
    ]:
        return self.additional_properties[key]

    def __setitem__(
        self,
        key: str,
        value: List[
            Union[
                "EmbedStep",
                "ErrorWorkflowStep",
                "EvaluateStep",
                "ForeachStep",
                "GetStep",
                "IfElseWorkflowStep",
                "LogStep",
                "ParallelStep",
                "PatchTaskRequestAdditionalPropertyItemType17",
                "PromptStep",
                "ReturnStep",
                "SearchStep",
                "SetStep",
                "SleepStep",
                "SwitchStep",
                "ToolCallStep",
                "WaitForInputStep",
                "YieldStep",
            ]
        ],
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
