from typing import Annotated, Any, Literal

from temporalio import workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from pydantic import BaseModel, Field, computed_field
    from pydantic_partial import create_partial_model

    from ...autogen.openapi_model import (
        CreateToolRequest,
        CreateTransitionRequest,
        ExecutionStatus,
        Tool,
        ToolRef,
        TransitionTarget,
        TransitionType,
        Workflow,
        WorkflowStep,
    )
    from ...worker.codec import RemoteObject

from ...queries.executions import list_execution_transitions
from ...queries.utils import serialize_model_data
from .models import ExecutionInput

# TODO: Maybe we should use a library for this

# State Machine
#
# init -> wait | error | step | cancelled | init_branch | finish
# init_branch -> wait | error | step | cancelled | finish_branch
# wait -> resume | error | cancelled
# resume -> wait | error | cancelled | step | finish | finish_branch | init_branch
# step -> wait | error | cancelled | step | finish | finish_branch | init_branch
# finish_branch -> wait | error | cancelled | step | finish | init_branch
# error ->

# Mermaid Diagram
# ```mermaid
# ---
# title: Execution state machine
# ---
# stateDiagram-v2
#     [*] --> queued
#     queued --> starting
#     queued --> cancelled
#     starting --> cancelled
#     starting --> failed
#     starting --> running
#     running --> running
#     running --> awaiting_input
#     running --> cancelled
#     running --> failed
#     running --> succeeded
#     awaiting_input --> running
#     awaiting_input --> cancelled
#     cancelled --> [*]
#     succeeded --> [*]
#     failed --> [*]

# ```
# TODO: figure out how to type this
valid_transitions: dict[TransitionType, list[TransitionType]] = {
    # Start state
    "init": ["wait", "error", "step", "cancelled", "init_branch", "finish"],
    "init_branch": [
        "wait",
        "error",
        "step",
        "cancelled",
        "init_branch",
        "finish_branch",
        "finish",
    ],
    # End states
    "finish": [],
    "error": [],
    "cancelled": [],
    # Intermediate states
    "wait": ["resume", "step", "cancelled", "finish", "finish_branch"],
    "resume": [
        "wait",
        "error",
        "cancelled",
        "step",
        "finish",
        "finish_branch",
        "init_branch",
    ],
    "step": [
        "wait",
        "error",
        "cancelled",
        "step",
        "finish",
        "finish_branch",
        "init_branch",
    ],
    "finish_branch": [
        "wait",
        "error",
        "cancelled",
        "step",
        "finish",
        "init_branch",
        "finish_branch",
    ],
}  # type: ignore

valid_previous_statuses: dict[ExecutionStatus, list[ExecutionStatus]] = {
    "running": ["starting", "awaiting_input", "running"],
    "starting": ["queued"],
    "queued": [],
    "awaiting_input": ["starting", "running"],
    "cancelled": ["queued", "starting", "awaiting_input", "running"],
    "succeeded": ["starting", "awaiting_input", "running"],
    "failed": ["starting", "running"],
}  # type: ignore

transition_to_execution_status: dict[TransitionType | None, ExecutionStatus] = {
    None: "queued",
    "init": "starting",
    "init_branch": "running",
    "wait": "awaiting_input",
    "resume": "running",
    "step": "running",
    "finish": "succeeded",
    "finish_branch": "running",
    "error": "failed",
    "cancelled": "cancelled",
}  # type: ignore


class PartialTransition(create_partial_model(CreateTransitionRequest)):
    user_state: dict[str, Any] = Field(default_factory=dict)


class StepContext(BaseModel):
    loaded: bool = False
    execution_input: ExecutionInput
    cursor: TransitionTarget
    current_input: Any | RemoteObject

    def load_inputs(self) -> None:
        self.execution_input.load_arguments()

        if isinstance(self.current_input, RemoteObject):
            self.current_input = self.current_input.load()

        self.loaded = True

    @computed_field
    @property
    def tools(self) -> list[Tool | CreateToolRequest]:
        execution_input = self.execution_input
        task = execution_input.task
        agent_tools = execution_input.agent_tools

        step_tools: Literal["all"] | list[ToolRef | CreateToolRequest] = getattr(
            self.current_step, "tools", "all"
        )

        if step_tools != "all":
            if not all(tool and isinstance(tool, CreateToolRequest) for tool in step_tools):
                msg = "Invalid tools for step (ToolRef not supported yet)"
                raise ApplicationError(msg)

            return step_tools

        # Need to convert task.tools (list[TaskToolDef]) to list[Tool]
        task_tools = []
        for tool in task.tools:
            tool_def = tool.model_dump()
            task_tools.append(
                CreateToolRequest(**{tool_def["type"]: tool_def.pop("spec"), **tool_def})
            )

        if not task.inherit_tools:
            return task_tools

        # Remove duplicates from agent_tools
        filtered_tools = [t for t in agent_tools if t.name not in (x.name for x in task.tools)]

        return filtered_tools + task_tools

    @computed_field
    @property
    def current_workflow(self) -> Annotated[Workflow, Field(exclude=True)]:
        workflows: list[Workflow] = self.execution_input.task.workflows
        return next(wf for wf in workflows if wf.name == self.cursor.workflow)

    @computed_field
    @property
    def current_step(self) -> Annotated[WorkflowStep, Field(exclude=True)]:
        return self.current_workflow.steps[self.cursor.step]

    @computed_field
    @property
    def is_last_step(self) -> Annotated[bool, Field(exclude=True)]:
        return (self.cursor.step + 1) == len(self.current_workflow.steps)

    @computed_field
    @property
    def is_first_step(self) -> Annotated[bool, Field(exclude=True)]:
        return self.cursor.step == 0

    @computed_field
    @property
    def is_main(self) -> Annotated[bool, Field(exclude=True)]:
        return self.cursor.workflow == "main"

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        dump = super().model_dump(*args, **kwargs)
        execution_input: dict = dump.pop("execution_input")

        return dump | execution_input

    async def get_inputs(self) -> tuple[list[Any], list[str | None]]:
        if self.execution_input.execution is None:
            return [], []

        transitions = await list_execution_transitions(
            execution_id=self.execution_input.execution.id,
            limit=1000,
            direction="asc",
        )  # type: ignore[not-callable]
        inputs = []
        labels = []
        for transition in transitions:
            if transition.next and transition.next.step >= len(inputs):
                inputs.append(transition.output)
                labels.append(transition.step_label)
        return inputs, labels

    async def prepare_for_step(self, *args, **kwargs) -> dict[str, Any]:
        current_input = self.current_input

        if isinstance(current_input, RemoteObject):
            current_input = current_input.load()

        current_input = serialize_model_data(current_input)

        inputs, labels = await self.get_inputs()
        labels = labels[1:]
        # Merge execution inputs into the dump dict
        dump = self.model_dump(*args, **kwargs)

        steps = {}
        for i, input in enumerate(inputs):
            step = {}
            step["input"] = input
            if i + 1 < len(inputs):
                step["output"] = inputs[i + 1]
                if labels[i]:
                    steps[labels[i]] = step

            steps[i] = step

        dump["steps"] = steps
        return dump | {"_": current_input}


class StepOutcome(BaseModel):
    error: str | None = None
    output: Any
    transition_to: tuple[TransitionType, TransitionTarget | RemoteObject] | None = None

    def load_remote(self) -> None:
        if isinstance(self.transition_to[1], RemoteObject):
            self.transition_to = (self.transition_to[0], self.transition_to[1].load())

        if isinstance(self.output, RemoteObject):
            self.output = self.output.load()

        if isinstance(self.error, RemoteObject):
            self.error = self.error.load()
