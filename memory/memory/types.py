from typing import Literal, Optional, TypedDict

###########
## Types ##
###########


class AssistantOutput(TypedDict):
    session_id: str
    assistant_output: str


class ChatMLMessage(TypedDict):
    name: Optional[str]
    role: Literal["assistant", "system", "user"]
    content: str


ChatML = list[ChatMLMessage]

# Example:
# [
#     {"role": "system", "name": "situation", "content": "I am talking to Diwank"},
#     {"role": "assistant", "name": "Samantha", "content": "Hey Diwank"},
#     {"role": "user", "name": "Diwank", "content": "Hey!"},
# ]
