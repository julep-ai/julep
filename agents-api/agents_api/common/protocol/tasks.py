from typing import Annotated, Any, Type
from uuid import UUID

from pydantic import BaseModel, Field, computed_field
from pydantic_partial import create_partial_model

from ...autogen.openapi_model import (
    Agent,
    CreateTaskRequest,
    CreateTransitionRequest,
    Execution,
    ExecutionStatus,
    PartialTaskSpecDef,
    PatchTaskRequest,
    Session,
    Task,
    TaskSpec,
    TaskSpecDef,
    TaskToolDef,
    Tool,
    TransitionTarget,
    TransitionType,
    UpdateTaskRequest,
    User,
    Workflow,
    WorkflowStep,
)

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

## Mermaid Diagram
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
    "init_branch": ["wait", "error", "step", "cancelled", "finish_branch"],
    # End states
    "finish": [],
    "error": [],
    "cancelled": [],
    # Intermediate states
    "wait": ["resume", "cancelled"],
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
    "finish_branch": ["wait", "error", "cancelled", "step", "finish", "init_branch"],
}  # type: ignore

valid_previous_statuses: dict[ExecutionStatus, list[ExecutionStatus]] = {
    "running": ["starting", "awaiting_input", "running"],
    "starting": ["queued"],
    "queued": [],
    "awaiting_input": ["starting", "running"],
    "cancelled": ["queued", "starting", "awaiting_input", "running"],
    "succeeded": ["starting", "running"],
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


PartialTransition: Type[BaseModel] = create_partial_model(CreateTransitionRequest)


class ExecutionInput(BaseModel):
    developer_id: UUID
    execution: Execution
    task: TaskSpecDef
    agent: Agent
    tools: list[Tool]
    arguments: dict[str, Any]

    # Not used at the moment
    user: User | None = None
    session: Session | None = None


class StepContext(BaseModel):
    execution_input: ExecutionInput
    inputs: list[Any]
    cursor: TransitionTarget

    @computed_field
    @property
    def outputs(self) -> list[dict[str, Any]]:  # included in dump
        return self.inputs[1:]

    @computed_field
    @property
    def current_input(self) -> dict[str, Any]:  # included in dump
        return self.inputs[-1]

    @computed_field
    @property
    def current_workflow(self) -> Annotated[Workflow, Field(exclude=True)]:
        workflows: list[Workflow] = self.execution_input.task.workflows
        return next(wf for wf in workflows if wf.name == self.cursor.workflow)

    @computed_field
    @property
    def current_step(self) -> Annotated[WorkflowStep, Field(exclude=True)]:
        step = self.current_workflow.steps[self.cursor.step]
        return step

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

        # Merge execution inputs into the dump dict
        execution_input: dict = dump.pop("execution_input")
        current_input: Any = dump.pop("current_input")
        dump = {
            **dump,
            **execution_input,
            "_": current_input,
        }

        return dump


class StepOutcome(BaseModel):
    error: str | None = None
    output: Any = None
    transition_to: tuple[TransitionType, TransitionTarget] | None = None


def task_to_spec(
    task: Task | CreateTaskRequest | UpdateTaskRequest | PatchTaskRequest, **model_opts
) -> TaskSpecDef | PartialTaskSpecDef:
    task_data = task.model_dump(**model_opts)
    main = task_data.pop("main")

    workflows = [Workflow(name="main", steps=main)]

    for k in list(task_data.keys()):
        if k in TaskSpec.model_fields.keys():
            continue

        steps = task_data.pop(k)
        workflows.append(Workflow(name=k, steps=steps))

    tools = task_data.pop("tools", [])
    tools = [TaskToolDef(spec=tool.pop(tool["type"]), **tool) for tool in tools]

    cls = PartialTaskSpecDef if isinstance(task, PatchTaskRequest) else TaskSpecDef

    return cls(
        workflows=workflows,
        tools=tools,
        **task_data,
    )


def spec_to_task_data(spec: dict) -> dict:
    task_id = spec.pop("task_id", None)

    workflows = spec.pop("workflows")
    workflows_dict = {workflow["name"]: workflow["steps"] for workflow in workflows}

    tools = spec.pop("tools", [])
    tools = [{tool["type"]: tool.pop("spec"), **tool} for tool in tools]

    return {
        "id": task_id,
        "tools": tools,
        **spec,
        **workflows_dict,
    }


def spec_to_task(**spec) -> Task | CreateTaskRequest:
    if not spec.get("id"):
        spec["id"] = spec.pop("task_id", None)

    if not spec.get("updated_at"):
        [updated_at_ms, _] = spec.pop("updated_at_ms", None)
        spec["updated_at"] = updated_at_ms and (updated_at_ms / 1000)

    cls = Task if spec["id"] else CreateTaskRequest
    return cls(**spec_to_task_data(spec))
