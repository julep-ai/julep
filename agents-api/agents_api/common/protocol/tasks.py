from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, computed_field

from ...autogen.openapi_model import (
    Agent,
    CreateTaskRequest,
    Execution,
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

valid_transitions = {
    # Start state
    "init": ["wait", "error", "step", "cancelled"],
    # End states
    "finish": [],
    "error": [],
    "cancelled": [],
    # Intermediate states
    "wait": ["resume", "error", "cancelled"],
    "resume": ["wait", "error", "step", "finish", "cancelled"],
    "step": ["wait", "error", "step", "finish", "cancelled"],
}

valid_previous_statuses = {
    "running": ["queued", "starting", "awaiting_input"],
    "cancelled": ["queued", "starting", "awaiting_input", "running"],
}

transition_to_execution_status = {
    "init": "queued",
    "wait": "awaiting_input",
    "resume": "running",
    "step": "running",
    "finish": "succeeded",
    "error": "failed",
    "cancelled": "cancelled",
}


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


WorkflowStepType = TypeVar("WorkflowStepType", bound=WorkflowStep)


class StepContext(BaseModel, Generic[WorkflowStepType]):
    execution_input: ExecutionInput
    inputs: list[dict[str, Any]]
    cursor: TransitionTarget

    @computed_field
    @property
    def outputs(self) -> list[dict[str, Any]]:
        return self.inputs[1:]

    @computed_field
    @property
    def current_input(self) -> dict[str, Any]:
        return self.inputs[-1]

    @computed_field
    @property
    def current_workflow(self) -> Workflow:
        workflows: list[Workflow] = self.execution_input.task.workflows
        return next(wf for wf in workflows if wf.name == self.cursor.workflow)

    @computed_field
    @property
    def current_step(self) -> WorkflowStepType:
        step = self.current_workflow[self.cursor.step]
        return step

    @computed_field
    @property
    def is_last_step(self) -> bool:
        return (self.cursor.step + 1) == len(self.current_workflow)

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        dump = super().model_dump(*args, **kwargs)
        dump["_"] = self.current_input

        return dump


OutcomeType = TypeVar("OutcomeType", bound=BaseModel)


class StepOutcome(BaseModel, Generic[OutcomeType]):
    output: OutcomeType | None
    transition_to: tuple[TransitionType, TransitionTarget] | None = None


def task_to_spec(
    task: Task | CreateTaskRequest | UpdateTaskRequest | PatchTaskRequest, **model_opts
) -> TaskSpecDef | PartialTaskSpecDef:
    task_data = task.model_dump(**model_opts)
    workflows = [Workflow(name="main", steps=task_data.pop("main"))]

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
