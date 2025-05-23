from typing import Any
from uuid import UUID

from beartype import beartype
from pydantic import BaseModel
from temporalio import workflow

from ...autogen.openapi_model import (
    Agent,
    CreateTaskRequest,
    CreateToolRequest,
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
)

with workflow.unsafe.imports_passed_through():
    from ...worker.codec import RemoteObject


# AIDEV-NOTE: Data model representing the input provided to a task execution workflow.
# Includes details about the developer, execution, task, agent, tools, and arguments.
class ExecutionInput(BaseModel):
    loaded: bool = False
    developer_id: UUID
    execution: Execution | None = None
    task: TaskSpecDef | None = None
    agent: Agent
    agent_tools: list[Tool | CreateToolRequest]
    arguments: dict[str, Any] | RemoteObject

    # AIDEV-TODO: Convert fields to only arguments (remote object only), execution_id, developer_id.
    # TODO: Convert fields to only arguments (remote object only), execution_id, developer_id

    # Not used at the moment
    user: User | None = None
    session: Session | None = None

    def load_arguments(self) -> None:
        if isinstance(self.arguments, RemoteObject):
            self.arguments = self.arguments.load()  # type: ignore
            self.loaded = True


@beartype
# AIDEV-NOTE: Converts a Task or task request model into a TaskSpecDef, which is used internally for workflow execution.
# Includes important notes on the conversion process and field renaming.
def task_to_spec(
    task: Task | CreateTaskRequest | UpdateTaskRequest | PatchTaskRequest,
    **model_opts,
) -> TaskSpecDef | PartialTaskSpecDef:
    """
    Converts a task to a task specification.

    IMPORTANT CONVERSION NOTES:
    - This conversion changes the structure of workflow steps
    - Raw task dictionaries use step types as keys (e.g., "if": condition)
    - Converted tasks use Pydantic models with kind_ field and renamed fields
      to avoid Python keywords:
      * "if" step becomes an IfElseWorkflowStep with kind_="if_else" and if_=condition
      * Fields like "if", "in", "from" get renamed to "if_", "in_", "from_"
      * These fields maintain their original names as aliases in the JSON

    This conversion is vital to understand when working with task validation,
    especially for expression validation which needs to handle both formats.
    """
    task_data = task.model_dump(
        **model_opts,
        exclude={"version", "developer_id", "task_id", "id", "agent_id"},
    )

    if "tools" in task_data:
        del task_data["tools"]

    tools = []
    for tool in task.tools:
        tool_spec = getattr(tool, tool.type)

        tool_obj = dict(
            type=tool.type,
            spec=tool_spec.model_dump(),
            **tool.model_dump(exclude={"type"}),
        )
        tools.append(TaskToolDef(**tool_obj))

    workflows = [Workflow(name="main", steps=task_data.pop("main"))]

    for key, steps in list(task_data.items()):
        if key not in TaskSpec.model_fields:
            workflows.append(Workflow(name=key, steps=steps))
            del task_data[key]

    cls = PartialTaskSpecDef if isinstance(task, PatchTaskRequest) else TaskSpecDef

    return cls(
        workflows=workflows,
        tools=tools,
        **task_data,
    )


# AIDEV-NOTE: Converts a TaskSpec dictionary back into a format suitable for Task or CreateTaskRequest models.
def spec_to_task_data(spec: dict) -> dict:
    task_id = spec.pop("task_id", None)

    workflows = spec.pop("workflows")
    workflows_dict = {workflow["name"]: workflow["steps"] for workflow in workflows}

    tools = spec.pop("tools", []) or []
    tools = [{tool["type"]: tool.pop("spec"), **tool} for tool in tools if tool]

    return {
        "id": task_id,
        "tools": tools,
        **spec,
        **workflows_dict,
    }


# AIDEV-NOTE: Converts a TaskSpec dictionary or arguments into a Task or CreateTaskRequest Pydantic model.
def spec_to_task(**spec) -> Task | CreateTaskRequest:
    if not spec.get("id"):
        spec["id"] = spec.pop("task_id", None)

    if not spec.get("updated_at"):
        [updated_at_ms, _] = spec.pop("updated_at_ms", None)
        spec["updated_at"] = updated_at_ms and (updated_at_ms / 1000)

    cls = Task if spec["id"] else CreateTaskRequest
    return cls(**spec_to_task_data(spec))
