from typing import Annotated, Any, List, Tuple
from uuid import UUID

from pydantic import BaseModel, Field

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
    UpdateTaskRequest,
    User,
    Workflow,
    WorkflowStep,
)


class ExecutionInput(BaseModel):
    developer_id: UUID
    execution: Execution
    task: TaskSpecDef
    agent: Agent
    tools: list[Tool]
    arguments: dict[str, Any]
    user: User | None = None
    session: Session | None = None


class StepContext(ExecutionInput):
    definition: WorkflowStep
    inputs: list[dict[str, Any]]

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        dump = super().model_dump(*args, **kwargs)

        dump["_"] = self.inputs[-1]
        dump["outputs"] = self.inputs[1:]

        return dump


class TransitionInfo(BaseModel):
    from_: Tuple[str, int]
    to: List[str | int] | None = None
    type: Annotated[str, Field(pattern="^(finish|wait|error|step)$")]
    outputs: dict[str, Any] | None = None


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
