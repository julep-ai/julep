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

from ..models.chat_input_tool_choice_type_0 import ChatInputToolChoiceType0
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_input_logit_bias import ChatInputLogitBias
    from ..models.chat_input_messages_item import ChatInputMessagesItem
    from ..models.named_api_call_choice import NamedApiCallChoice
    from ..models.named_function_choice import NamedFunctionChoice
    from ..models.named_integration_choice import NamedIntegrationChoice
    from ..models.named_system_choice import NamedSystemChoice
    from ..models.schema_completion_response_format import (
        SchemaCompletionResponseFormat,
    )
    from ..models.simple_completion_response_format import (
        SimpleCompletionResponseFormat,
    )
    from ..models.tool import Tool


T = TypeVar("T", bound="ChatInput")


@_attrs_define
class ChatInput:
    """
    Attributes:
        messages (List['ChatInputMessagesItem']): A list of new input messages comprising the conversation so far.
        tools (List['Tool']): (Advanced) List of tools that are provided in addition to agent's default set of tools.
        remember (bool): DISABLED: Whether this interaction should form new memories or not (will be enabled in a future
            release) Default: False.
        recall (bool): Whether previous memories and docs should be recalled or not Default: True.
        save (bool): Whether this interaction should be stored in the session history or not Default: True.
        stream (bool): Indicates if the server should stream the response as it's generated Default: False.
        stop (List[str]): Up to 4 sequences where the API will stop generating further tokens.
        tool_choice (Union['NamedApiCallChoice', 'NamedFunctionChoice', 'NamedIntegrationChoice', 'NamedSystemChoice',
            ChatInputToolChoiceType0, Unset]): Can be one of existing tools given to the agent earlier or the ones provided
            in this request.
        frequency_penalty (Union[Unset, float]): Number between -2.0 and 2.0. Positive values penalize new tokens based
            on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line
            verbatim.
        presence_penalty (Union[Unset, float]): Number between -2.0 and 2.0. Positive values penalize new tokens based
            on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line
            verbatim.
        temperature (Union[Unset, float]): What sampling temperature to use, between 0 and 2. Higher values like 0.8
            will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
        top_p (Union[Unset, float]): Defaults to 1 An alternative to sampling with temperature, called nucleus sampling,
            where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens
            comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but
            not both.
        repetition_penalty (Union[Unset, float]): Number between 0 and 2.0. 1.0 is neutral and values larger than that
            penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to
            repeat the same line verbatim.
        length_penalty (Union[Unset, float]): Number between 0 and 2.0. 1.0 is neutral and values larger than that
            penalize number of tokens generated.
        min_p (Union[Unset, float]): Minimum probability compared to leading token to be considered
        model (Union[Unset, str]): For Unicode character safety
            See: https://unicode.org/reports/tr31/
            See: https://www.unicode.org/reports/tr39/#Identifier_Characters
        seed (Union[Unset, int]): If specified, the system will make a best effort to sample deterministically for that
            particular seed value
        max_tokens (Union[Unset, int]): The maximum number of tokens to generate in the chat completion
        logit_bias (Union[Unset, ChatInputLogitBias]): Modify the likelihood of specified tokens appearing in the
            completion
        response_format (Union['SchemaCompletionResponseFormat', 'SimpleCompletionResponseFormat', Unset]): Response
            format (set to `json_object` to restrict output to JSON)
        agent (Union[Unset, str]):
    """

    messages: List["ChatInputMessagesItem"]
    tools: List["Tool"]
    stop: List[str]
    remember: bool = False
    recall: bool = True
    save: bool = True
    stream: bool = False
    tool_choice: Union[
        "NamedApiCallChoice",
        "NamedFunctionChoice",
        "NamedIntegrationChoice",
        "NamedSystemChoice",
        ChatInputToolChoiceType0,
        Unset,
    ] = UNSET
    frequency_penalty: Union[Unset, float] = UNSET
    presence_penalty: Union[Unset, float] = UNSET
    temperature: Union[Unset, float] = UNSET
    top_p: Union[Unset, float] = UNSET
    repetition_penalty: Union[Unset, float] = UNSET
    length_penalty: Union[Unset, float] = UNSET
    min_p: Union[Unset, float] = UNSET
    model: Union[Unset, str] = UNSET
    seed: Union[Unset, int] = UNSET
    max_tokens: Union[Unset, int] = UNSET
    logit_bias: Union[Unset, "ChatInputLogitBias"] = UNSET
    response_format: Union[
        "SchemaCompletionResponseFormat", "SimpleCompletionResponseFormat", Unset
    ] = UNSET
    agent: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.chat_input_logit_bias import ChatInputLogitBias
        from ..models.chat_input_messages_item import ChatInputMessagesItem
        from ..models.named_api_call_choice import NamedApiCallChoice
        from ..models.named_function_choice import NamedFunctionChoice
        from ..models.named_integration_choice import NamedIntegrationChoice
        from ..models.named_system_choice import NamedSystemChoice
        from ..models.schema_completion_response_format import (
            SchemaCompletionResponseFormat,
        )
        from ..models.simple_completion_response_format import (
            SimpleCompletionResponseFormat,
        )
        from ..models.tool import Tool

        messages = []
        for messages_item_data in self.messages:
            messages_item = messages_item_data.to_dict()
            messages.append(messages_item)

        tools = []
        for tools_item_data in self.tools:
            tools_item = tools_item_data.to_dict()
            tools.append(tools_item)

        remember = self.remember

        recall = self.recall

        save = self.save

        stream = self.stream

        stop = self.stop

        tool_choice: Union[Dict[str, Any], Unset, str]
        if isinstance(self.tool_choice, Unset):
            tool_choice = UNSET
        elif isinstance(self.tool_choice, ChatInputToolChoiceType0):
            tool_choice = self.tool_choice.value
        elif isinstance(self.tool_choice, NamedFunctionChoice):
            tool_choice = self.tool_choice.to_dict()
        elif isinstance(self.tool_choice, NamedIntegrationChoice):
            tool_choice = self.tool_choice.to_dict()
        elif isinstance(self.tool_choice, NamedSystemChoice):
            tool_choice = self.tool_choice.to_dict()
        else:
            tool_choice = self.tool_choice.to_dict()

        frequency_penalty = self.frequency_penalty

        presence_penalty = self.presence_penalty

        temperature = self.temperature

        top_p = self.top_p

        repetition_penalty = self.repetition_penalty

        length_penalty = self.length_penalty

        min_p = self.min_p

        model = self.model

        seed = self.seed

        max_tokens = self.max_tokens

        logit_bias: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.logit_bias, Unset):
            logit_bias = self.logit_bias.to_dict()

        response_format: Union[Dict[str, Any], Unset]
        if isinstance(self.response_format, Unset):
            response_format = UNSET
        elif isinstance(self.response_format, SimpleCompletionResponseFormat):
            response_format = self.response_format.to_dict()
        else:
            response_format = self.response_format.to_dict()

        agent = self.agent

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "messages": messages,
                "tools": tools,
                "remember": remember,
                "recall": recall,
                "save": save,
                "stream": stream,
                "stop": stop,
            }
        )
        if tool_choice is not UNSET:
            field_dict["tool_choice"] = tool_choice
        if frequency_penalty is not UNSET:
            field_dict["frequency_penalty"] = frequency_penalty
        if presence_penalty is not UNSET:
            field_dict["presence_penalty"] = presence_penalty
        if temperature is not UNSET:
            field_dict["temperature"] = temperature
        if top_p is not UNSET:
            field_dict["top_p"] = top_p
        if repetition_penalty is not UNSET:
            field_dict["repetition_penalty"] = repetition_penalty
        if length_penalty is not UNSET:
            field_dict["length_penalty"] = length_penalty
        if min_p is not UNSET:
            field_dict["min_p"] = min_p
        if model is not UNSET:
            field_dict["model"] = model
        if seed is not UNSET:
            field_dict["seed"] = seed
        if max_tokens is not UNSET:
            field_dict["max_tokens"] = max_tokens
        if logit_bias is not UNSET:
            field_dict["logit_bias"] = logit_bias
        if response_format is not UNSET:
            field_dict["response_format"] = response_format
        if agent is not UNSET:
            field_dict["agent"] = agent

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.chat_input_logit_bias import ChatInputLogitBias
        from ..models.chat_input_messages_item import ChatInputMessagesItem
        from ..models.named_api_call_choice import NamedApiCallChoice
        from ..models.named_function_choice import NamedFunctionChoice
        from ..models.named_integration_choice import NamedIntegrationChoice
        from ..models.named_system_choice import NamedSystemChoice
        from ..models.schema_completion_response_format import (
            SchemaCompletionResponseFormat,
        )
        from ..models.simple_completion_response_format import (
            SimpleCompletionResponseFormat,
        )
        from ..models.tool import Tool

        d = src_dict.copy()
        messages = []
        _messages = d.pop("messages")
        for messages_item_data in _messages:
            messages_item = ChatInputMessagesItem.from_dict(messages_item_data)

            messages.append(messages_item)

        tools = []
        _tools = d.pop("tools")
        for tools_item_data in _tools:
            tools_item = Tool.from_dict(tools_item_data)

            tools.append(tools_item)

        remember = d.pop("remember")

        recall = d.pop("recall")

        save = d.pop("save")

        stream = d.pop("stream")

        stop = cast(List[str], d.pop("stop"))

        def _parse_tool_choice(
            data: object,
        ) -> Union[
            "NamedApiCallChoice",
            "NamedFunctionChoice",
            "NamedIntegrationChoice",
            "NamedSystemChoice",
            ChatInputToolChoiceType0,
            Unset,
        ]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                tool_choice_type_0 = ChatInputToolChoiceType0(data)

                return tool_choice_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                tool_choice_type_1 = NamedFunctionChoice.from_dict(data)

                return tool_choice_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                tool_choice_type_2 = NamedIntegrationChoice.from_dict(data)

                return tool_choice_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                tool_choice_type_3 = NamedSystemChoice.from_dict(data)

                return tool_choice_type_3
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            tool_choice_type_4 = NamedApiCallChoice.from_dict(data)

            return tool_choice_type_4

        tool_choice = _parse_tool_choice(d.pop("tool_choice", UNSET))

        frequency_penalty = d.pop("frequency_penalty", UNSET)

        presence_penalty = d.pop("presence_penalty", UNSET)

        temperature = d.pop("temperature", UNSET)

        top_p = d.pop("top_p", UNSET)

        repetition_penalty = d.pop("repetition_penalty", UNSET)

        length_penalty = d.pop("length_penalty", UNSET)

        min_p = d.pop("min_p", UNSET)

        model = d.pop("model", UNSET)

        seed = d.pop("seed", UNSET)

        max_tokens = d.pop("max_tokens", UNSET)

        _logit_bias = d.pop("logit_bias", UNSET)
        logit_bias: Union[Unset, ChatInputLogitBias]
        if isinstance(_logit_bias, Unset):
            logit_bias = UNSET
        else:
            logit_bias = ChatInputLogitBias.from_dict(_logit_bias)

        def _parse_response_format(
            data: object,
        ) -> Union[
            "SchemaCompletionResponseFormat", "SimpleCompletionResponseFormat", Unset
        ]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_format_type_0 = SimpleCompletionResponseFormat.from_dict(data)

                return response_format_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_format_type_1 = SchemaCompletionResponseFormat.from_dict(data)

            return response_format_type_1

        response_format = _parse_response_format(d.pop("response_format", UNSET))

        agent = d.pop("agent", UNSET)

        chat_input = cls(
            messages=messages,
            tools=tools,
            remember=remember,
            recall=recall,
            save=save,
            stream=stream,
            stop=stop,
            tool_choice=tool_choice,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            length_penalty=length_penalty,
            min_p=min_p,
            model=model,
            seed=seed,
            max_tokens=max_tokens,
            logit_bias=logit_bias,
            response_format=response_format,
            agent=agent,
        )

        chat_input.additional_properties = d
        return chat_input

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
