# ruff: noqa: F401, F403, F405
from typing import Annotated, Any, Generic, Literal, Self, Type, TypeVar, get_args
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


class CreateToolRequest(UpdateToolRequest):
    pass


class CreateOrUpdateAgentRequest(UpdateAgentRequest):
    pass


class CreateOrUpdateUserRequest(UpdateUserRequest):
    pass


class CreateOrUpdateSessionRequest(CreateSessionRequest):
    pass


ChatResponse = ChunkChatResponse | MessageChatResponse


class MapReduceStep(Main):
    pass


class ChatMLTextContentPart(Content):
    pass


class ChatMLImageContentPart(ContentModel):
    pass


class InputChatMLMessage(Message):
    pass


# Custom types (not generated correctly)
# --------------------------------------

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

# Extract ChatMLRole
ChatMLRole = BaseEntry.model_fields["role"].annotation

# Extract ChatMLSource
ChatMLSource = BaseEntry.model_fields["source"].annotation

# Extract ExecutionStatus
ExecutionStatus = Execution.model_fields["status"].annotation

# Extract TransitionType
TransitionType = Transition.model_fields["type"].annotation

# Assertions to ensure consistency (optional, but recommended for runtime checks)
assert ChatMLRole == BaseEntry.model_fields["role"].annotation
assert ChatMLSource == BaseEntry.model_fields["source"].annotation
assert ExecutionStatus == Execution.model_fields["status"].annotation
assert TransitionType == Transition.model_fields["type"].annotation


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


# Workflow related models
# -----------------------

WorkflowStep = (
    EvaluateStep
    | ToolCallStep
    | PromptStep
    | GetStep
    | SetStep
    | LogStep
    | EmbedStep
    | SearchStep
    | ReturnStep
    | SleepStep
    | ErrorWorkflowStep
    | YieldStep
    | WaitForInputStep
    | IfElseWorkflowStep
    | SwitchStep
    | ForeachStep
    | ParallelStep
    | MapReduceStep
)


class Workflow(BaseModel):
    name: str
    steps: list[WorkflowStep]


# Task spec helper models
# ----------------------


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


# Patch some models to allow extra fields
# --------------------------------------


_CreateTaskRequest = CreateTaskRequest


class CreateTaskRequest(_CreateTaskRequest):
    model_config = ConfigDict(
        **{
            **_CreateTaskRequest.model_config,
            "extra": "allow",
        }
    )


CreateOrUpdateTaskRequest = CreateTaskRequest

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
