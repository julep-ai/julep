from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from ...autogen.openapi_model import (
    Agent,
    Execution,
    PromptWorkflowStep,
    EvaluateWorkflowStep,
    YieldWorkflowStep,
    ToolCallWorkflowStep,
    ErrorWorkflowStep,
    IfElseWorkflowStep,
    Session,
    Task,
    Tool,
    User,
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

    # FIXME: Create a unified type for this union
    steps: list[WorkflowStep]


class TaskSpec(BaseModel):
    name: str
    description: str
    tools_available: list[str] | Literal["all"]
    input_schema: dict[str, Any]
    workflows: list[TaskWorkflow]


class TaskProtocol(SerializableTask):
    @property
    def spec(self) -> TaskSpec:
        workflows = [
            TaskWorkflow(name="main", steps=self.main),
            # ... others
        ] + [
            TaskWorkflow(name=workflow_name, steps=workflow_steps)
            for workflow_name, workflow_steps in self.model_extra.items()
        ]

        return TaskSpec(
            name=self.name,
            description=self.description,
            tools_available=self.tools_available,
            input_schema=self.input_schema,
            workflows=workflows,
        )


class ExecutionInput(BaseModel):
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
