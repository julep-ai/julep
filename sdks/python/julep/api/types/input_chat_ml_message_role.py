# This file was auto-generated by Fern from our API Definition.

import enum
import typing

T_Result = typing.TypeVar("T_Result")


class InputChatMlMessageRole(str, enum.Enum):
    """
    ChatML role (system|assistant|user|function_call|function|auto)
    """

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION_CALL = "function_call"
    FUNCTION = "function"
    AUTO = "auto"

    def visit(
        self,
        user: typing.Callable[[], T_Result],
        assistant: typing.Callable[[], T_Result],
        system: typing.Callable[[], T_Result],
        function_call: typing.Callable[[], T_Result],
        function: typing.Callable[[], T_Result],
        auto: typing.Callable[[], T_Result],
    ) -> T_Result:
        if self is InputChatMlMessageRole.USER:
            return user()
        if self is InputChatMlMessageRole.ASSISTANT:
            return assistant()
        if self is InputChatMlMessageRole.SYSTEM:
            return system()
        if self is InputChatMlMessageRole.FUNCTION_CALL:
            return function_call()
        if self is InputChatMlMessageRole.FUNCTION:
            return function()
        if self is InputChatMlMessageRole.AUTO:
            return auto()
