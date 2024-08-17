# ruff: noqa: F401, F403, F405
from typing import Annotated, Any, Generic, Literal, Self, Type, TypeVar
from uuid import UUID

from litellm.utils import _select_tokenizer as select_tokenizer
from litellm.utils import token_counter
from pydantic import AwareDatetime, Field

from ..common.utils.datetime import utcnow
from .Agents import *
from .Chat import *
from .Common import *
from .Docs import *
from .Entries import *
from .Executions import *
from .Jobs import *
from .Sessions import *
from .Tasks import *
from .Tools import *
from .Users import *

# Generic models
# --------------

DataT = TypeVar("DataT", bound=BaseModel)


class ListResponse(BaseModel, Generic[DataT]):
    items: list[DataT]


# Aliases
# -------

CreateToolRequest = UpdateToolRequest
CreateOrUpdateAgentRequest = UpdateAgentRequest
CreateOrUpdateUserRequest = UpdateUserRequest
CreateOrUpdateSessionRequest = CreateSessionRequest
CreateOrUpdateTaskRequest = CreateTaskRequest
ChatResponse = ChunkChatResponse | MessageChatResponse


# Custom types (not generated correctly)
# --------------------------------------

# TODO: Remove these when auto-population is fixed

ChatMLContent = (
    list[ChatMLTextContentPart | ChatMLImageContentPart]
    | Tool
    | ChosenToolCall
    | str
    | ToolResponse
    | list[
        list[ChatMLTextContentPart | ChatMLImageContentPart]
        | Tool
        | ChosenToolCall
        | str
        | ToolResponse
    ]
)

ChatMLRole = Literal[
    "user",
    "assistant",
    "system",
    "function",
    "function_response",
    "function_call",
    "auto",
]
assert BaseEntry.model_fields["role"].annotation == ChatMLRole

ChatMLSource = Literal[
    "api_request", "api_response", "tool_response", "internal", "summarizer", "meta"
]
assert BaseEntry.model_fields["source"].annotation == ChatMLSource


ExecutionStatus = Literal[
    "queued",
    "starting",
    "running",
    "awaiting_input",
    "succeeded",
    "failed",
    "cancelled",
]
assert Execution.model_fields["status"].annotation == ExecutionStatus


TransitionType = Literal["finish", "wait", "resume", "error", "step", "cancelled"]
assert Transition.model_fields["type"].annotation == TransitionType


# Create models
# -------------


class CreateTransitionRequest(Transition):
    # The following fields are optional in this

    id: UUID | None = None
    execution_id: UUID | None = None
    created_at: AwareDatetime | None = None
    updated_at: AwareDatetime | None = None
    metadata: dict[str, Any] | None = None


class CreateEntryRequest(BaseEntry):
    timestamp: Annotated[
        float, Field(ge=0.0, default_factory=lambda: utcnow().timestamp())
    ]

    @classmethod
    def from_model_input(
        cls: Type[Self],
        model: str,
        *,
        role: ChatMLRole,
        content: ChatMLContent,
        name: str | None = None,
        source: ChatMLSource,
        **kwargs: dict,
    ) -> Self:
        tokenizer: dict = select_tokenizer(model=model)
        token_count = token_counter(
            model=model, messages=[{"role": role, "content": content, "name": name}]
        )

        return cls(
            role=role,
            content=content,
            name=name,
            source=source,
            tokenizer=tokenizer["type"],
            token_count=token_count,
            **kwargs,
        )


# Task related models
# -------------------

WorkflowStep = (
    PromptStep
    | EvaluateStep
    | YieldStep
    | ToolCallStep
    | ErrorWorkflowStep
    | IfElseWorkflowStep
)


class Workflow(BaseModel):
    name: str
    steps: list[WorkflowStep]


class TaskToolDef(BaseModel):
    type: str
    name: str
    spec: dict
    inherited: bool = False


_Task = Task


class TaskSpec(_Task):
    model_config = ConfigDict(extra="ignore")

    workflows: list[Workflow]

    # Remove main field from the model
    main: None = None


class TaskSpecDef(TaskSpec):
    id: UUID | None = None
    created_at: AwareDatetime | None = None
    updated_at: AwareDatetime | None = None


class PartialTaskSpecDef(TaskSpecDef):
    name: str | None = None


class Task(_Task):
    model_config = ConfigDict(
        **{
            **_Task.model_config,
            "extra": "allow",
        }
    )


_CreateTaskRequest = CreateTaskRequest


class CreateTaskRequest(_CreateTaskRequest):
    model_config = ConfigDict(
        **{
            **_CreateTaskRequest.model_config,
            "extra": "allow",
        }
    )


_PatchTaskRequest = PatchTaskRequest


class PatchTaskRequest(_PatchTaskRequest):
    model_config = ConfigDict(
        **{
            **_PatchTaskRequest.model_config,
            "extra": "allow",
        }
    )


_UpdateTaskRequest = UpdateTaskRequest


class UpdateTaskRequest(_UpdateTaskRequest):
    model_config = ConfigDict(
        **{
            **_UpdateTaskRequest.model_config,
            "extra": "allow",
        }
    )
