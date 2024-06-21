from datetime import datetime
from typing import Annotated, Any, List, Literal, Tuple

from pydantic import BaseModel, Field, UUID4, computed_field

from ...autogen.openapi_model import (
    User,
    Agent,
    Session,
    Tool,
    FunctionDef,
    PromptWorkflowStep,
    EvaluateWorkflowStep,
    YieldWorkflowStep,
    ToolCallWorkflowStep,
    ErrorWorkflowStep,
    IfElseWorkflowStep,
    Task,
    Execution,
)

from ...models.execution.get_execution_input import get_execution_input_query
from ..utils.cozo import uuid_int_list_to_uuid4

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
    @classmethod
    def from_cozo_data(cls, task_data: dict[str, Any]) -> "SerializableTask":

        workflows = task_data.pop("workflows")
        assert len(workflows) > 0

        main_wf_idx, main_wf = next(
            (i, wf) for i, wf in enumerate(workflows) if wf["name"] == "main"
        )

        task_data["main"] = main_wf["steps"]
        workflows.pop(main_wf_idx)

        for workflow in workflows:
            task_data[workflow["name"]] = workflow["steps"]

        return cls(**task_data)

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


class ExecutionInput(BaseModel):
    developer_id: UUID4
    execution: Execution
    task: TaskProtocol
    agent: Agent
    user: User | None
    session: Session | None
    tools: list[Tool]
    arguments: dict[str, Any]

    @classmethod
    def fetch(
        cls, *, developer_id: UUID4, task_id: UUID4, execution_id: UUID4, client: Any
    ) -> "ExecutionInput":
        [data] = get_execution_input_query(
            task_id=task_id,
            execution_id=execution_id,
            client=client,
        ).to_dict(orient="records")

        # FIXME: Need to manually convert id from list of int to UUID4
        # because cozo has a bug with UUID4
        # See: https://github.com/cozodb/cozo/issues/269
        for kind in ["task", "execution", "agent", "user", "session"]:
            if not data[kind]:
                continue

            for key in data[kind]:
                if key == "id" or key.endswith("_id") and data[kind][key] is not None:
                    data[kind][key] = uuid_int_list_to_uuid4(data[kind][key])

        agent = Agent(**data["agent"])
        task = TaskProtocol.from_cozo_data(data["task"])
        execution = Execution(**data["execution"])
        user = User(**data["user"]) if data["user"] else None
        session = Session(**data["session"]) if data["session"] else None
        tools = [
            Tool(type="function", id=function["id"], function=FunctionDef(**function))
            for function in data["tools"]
        ]
        arguments = execution.arguments

        return cls(
            developer_id=developer_id,
            execution=execution,
            task=task,
            agent=agent,
            user=user,
            session=session,
            tools=tools,
            arguments=arguments,
        )


class StepContext(ExecutionInput):
    definition: WorkflowStep
    inputs: list[dict[str, Any]]

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        dump = super().model_dump(*args, **kwargs)

        dump["$"] = self.inputs[-1]
        dump["outputs"] = self.inputs[1:]

        return dump


class TransitionInfo(BaseModel):
    from_: Tuple[str, int]
    to: List[str | int] | None = None
    type: Annotated[str, Field(pattern="^(finish|wait|error|step)$")]
    outputs: dict[str, Any] | None = None
