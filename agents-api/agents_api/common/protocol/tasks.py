from datetime import datetime
from typing import Annotated, Any, List, Literal

from pydantic import BaseModel, Field, UUID4, computed_field

from ...autogen.openapi_model import (
    PromptWorkflowStep,
    EvaluateWorkflowStep,
    YieldWorkflowStep,
    ToolCallWorkflowStep,
    ErrorWorkflowStep,
    IfElseWorkflowStep,
    Task,
)

WorkflowStep = (
    PromptWorkflowStep
    | EvaluateWorkflowStep
    | YieldWorkflowStep
    | ToolCallWorkflowStep
    | ErrorWorkflowStep
    | IfElseWorkflowStep
)


# Make Task serializable (created_at is a datetime)
class SerializableTask(Task):
    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        dump = super().model_dump(*args, **kwargs)
        dump["created_at"] = self.created_at.isoformat()

        return dump

    # And load it back
    @classmethod
    def model_load(cls, data: dict[str, Any], *args, **kwargs) -> "SerializableTask":
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return super().model_load(data, *args, **kwargs)


class TaskWorkflow(BaseModel):
    name: str
    steps: list[WorkflowStep]


class TaskSpec(BaseModel):
    name: str | None
    description: str | None
    tools_available: list[str] | Literal["all"] | None = "all"
    input_schema: dict[str, Any] | None = {}
    workflows: list[TaskWorkflow]


class TaskProtocol(SerializableTask):
    @computed_field
    @property
    def spec(self) -> TaskSpec:
        other_workflows = {
            workflow_name: getattr(self, workflow_name)
            for workflow_name in self.model_extra.keys()
            if workflow_name not in Task.model_fields.keys() and workflow_name != "spec"
        }

        workflows = [
            TaskWorkflow(name="main", steps=self.main),
            # ... others
        ] + [
            TaskWorkflow(name=workflow_name, steps=workflow_steps)
            for workflow_name, workflow_steps in other_workflows.items()
        ]

        return TaskSpec(
            name=self.name,
            description=self.description,
            tools_available=self.tools_available,
            input_schema=self.input_schema,
            workflows=workflows,
        )


# FIXME: Enable all of these
class ExecutionInput(BaseModel):
    developer_id: UUID4
    # execution: Execution
    task: TaskProtocol
    # agent: Agent
    # user: User | None
    # session: Session | None
    # tools: list[Tool]
    arguments: dict[str, Any]


class StepContext(ExecutionInput):
    definition: WorkflowStep
    inputs: list[dict[str, Any]]

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        dump = super().model_dump(*args, **kwargs)

        dump["$"] = self.inputs[-1]
        dump["outputs"] = self.inputs[1:]

        return dump


class TransitionInfo(BaseModel):
    from_: Annotated[List[str | int], Field(alias="from")]
    to: List[str | int]
    type: Annotated[str, Field(pattern="^(finish|wait|error|step)$")]
    outputs: dict[str, Any]
