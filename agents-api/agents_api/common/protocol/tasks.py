import asyncio
from typing import Annotated, Any, Literal
from uuid import UUID

from temporalio import workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from pydantic import BaseModel, Field, computed_field
    from pydantic_partial import create_partial_model

    from ...activities.task_steps.base_evaluate import base_evaluate
    from ...activities.task_steps.secret_storage import SecretStorage
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

from ...env import max_steps_accessible_in_tasks
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


class WorkflowResult(BaseModel):
    """
    Represents the result of a workflow execution, including metadata about how it was completed.
    """

    state: PartialTransition
    returned: bool = (
        False  # True if execution of a sub-workflow ended due to a return statement
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


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
        secrets = SecretStorage()
        execution_input = self.execution_input
        task = execution_input.task
        agent_tools = execution_input.agent_tools

        step_tools: Literal["all"] | list[ToolRef | CreateToolRequest] = getattr(
            self.current_step,
            "tools",
            "all",
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
            spec = tool_def.pop("spec", {}) or {}
            evaluated_spec = asyncio.run(base_evaluate(spec, values={"secrets": secrets}))
            task_tools.append(
                CreateToolRequest(**{tool_def["type"]: evaluated_spec, **tool_def}),
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
    def current_scope_id(self) -> Annotated[UUID, Field(exclude=True)]:
        return self.cursor.scope_id

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

    async def get_inputs(
        self, limit: int = 50
    ) -> tuple[list[Any], list[str | None], dict[str, Any]]:
        if self.execution_input.execution is None:
            return [], [], {}

        inputs = []
        labels = []
        state = {}
        scope_id = self.current_scope_id

        transitions = await list_execution_transitions(
            execution_id=self.execution_input.execution.id,
            limit=limit,
            direction="asc",
            scope_id=scope_id,
        )  # type: ignore[not-callable]
        assert len(transitions) > 0, "No transitions found"

        for transition in transitions:
            # NOTE: The length hack should be refactored in case we want to implement multi-step control steps
            if transition.next and transition.next.step >= len(inputs):
                inputs.append(transition.output)
                labels.append(transition.step_label)
            if transition.metadata and transition.metadata.get("step_type") == "SetStep":
                state.update(transition.output)

        return inputs, labels, state

    async def prepare_for_step(
        self, limit: int = max_steps_accessible_in_tasks, *args, **kwargs
    ) -> dict[str, Any]:
        current_input = self.current_input

        if isinstance(current_input, RemoteObject):
            current_input = current_input.load()

        current_input = serialize_model_data(current_input)

        inputs, labels, state = await self.get_inputs(limit=limit)
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

        dump["state"] = state
        dump["steps"] = steps
        dump["inputs"] = {i: step["input"] for i, step in steps.items()}
        dump["outputs"] = {i: step["output"] for i, step in steps.items() if "output" in step}
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
