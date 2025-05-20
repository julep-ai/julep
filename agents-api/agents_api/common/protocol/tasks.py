from datetime import timedelta
from typing import Annotated, Any, Literal
from uuid import UUID

from temporalio import workflow
from temporalio.exceptions import ApplicationError
from temporalio.workflow import _NotInWorkflowEventLoopError

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
    from ...common.utils.expressions import evaluate_expressions
    from ...worker.codec import RemoteObject

from ...activities.pg_query_step import pg_query_step
from ...common.retry_policies import DEFAULT_RETRY_POLICY
from ...env import max_steps_accessible_in_tasks, temporal_heartbeat_timeout
from ...queries.executions import (
    list_execution_inputs_data,
    list_execution_state_data,
)
from ...queries.secrets.list import list_secrets_query
from ...queries.utils import serialize_model_data
from .models import ExecutionInput

# AIDEV-TODO: Maybe we should use a library for this state machine logic.

# AIDEV-NOTE: Defines the valid state transitions for task executions.
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

# AIDEV-NOTE: Maps valid previous execution statuses for each current status.
valid_previous_statuses: dict[ExecutionStatus, list[ExecutionStatus]] = {
    "running": ["starting", "awaiting_input", "running"],
    "starting": ["queued"],
    "queued": [],
    "awaiting_input": ["starting", "running"],
    "cancelled": ["queued", "starting", "awaiting_input", "running"],
    "succeeded": ["starting", "awaiting_input", "running"],
    "failed": ["starting", "running"],
}  # type: ignore

# AIDEV-NOTE: Maps transition types to corresponding execution statuses.
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


# AIDEV-NOTE: Represents a partial state transition during task execution.
class PartialTransition(create_partial_model(CreateTransitionRequest)):
    user_state: dict[str, Any] = Field(default_factory=dict)


# AIDEV-NOTE: Represents the result and metadata of a workflow execution.
class WorkflowResult(BaseModel):
    """
    Represents the result of a workflow execution, including metadata about how it was completed.
    """

    state: PartialTransition
    returned: bool = (
        False  # True if execution of a sub-workflow ended due to a return statement
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


# AIDEV-NOTE: Provides context for the current step execution, including execution input, cursor, and current input.
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

    # AIDEV-NOTE: To get the tools available for the current step, considering agent and task tools.
    async def tools(self) -> list[Tool | CreateToolRequest]:
        execution_input = self.execution_input
        task = execution_input.task
        agent_tools = execution_input.agent_tools
        secrets = {}

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
        tools = task.tools if task else []
        inherit_tools = task.inherit_tools if task else False
        try:
            secrets_query_result = await workflow.execute_activity(
                pg_query_step,
                args=[
                    "list_secrets_query",
                    "secrets.list",
                    {"developer_id": self.execution_input.developer_id, "decrypt": True},
                ],
                schedule_to_close_timeout=timedelta(days=31),
                retry_policy=DEFAULT_RETRY_POLICY,
                heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
            )
        except _NotInWorkflowEventLoopError:
            secrets_query_result = await list_secrets_query(
                developer_id=self.execution_input.developer_id,
                decrypt=True,
            )

        if tools:
            secrets = {secret.name: secret.value for secret in secrets_query_result}
        for tool in tools:
            tool_def = tool.model_dump()
            spec = tool_def.pop("spec", {}) or {}
            evaluated_spec = (
                evaluate_expressions(spec, values={"secrets": secrets}) if spec else {}
            )
            task_tools.append(
                CreateToolRequest(**{tool_def["type"]: evaluated_spec, **tool_def}),
            )

        if not inherit_tools:
            return task_tools

        # Remove duplicates from agent_tools
        filtered_tools = [t for t in agent_tools if t.name not in (x.name for x in tools)]

        return filtered_tools + task_tools

    @computed_field
    @property
    # AIDEV-NOTE: Computed property to get the current workflow based on the cursor.
    def current_workflow(self) -> Annotated[Workflow, Field(exclude=True)]:
        workflows: list[Workflow] = self.execution_input.task.workflows
        return next(wf for wf in workflows if wf.name == self.cursor.workflow)

    @computed_field
    @property
    # AIDEV-NOTE: Computed property to get the current step definition based on the cursor.
    def current_step(self) -> Annotated[WorkflowStep, Field(exclude=True)]:
        return self.current_workflow.steps[self.cursor.step]

    @computed_field
    @property
    # AIDEV-NOTE: Computed property to get the current scope ID from the cursor.
    def current_scope_id(self) -> Annotated[UUID, Field(exclude=True)]:
        return self.cursor.scope_id

    @computed_field
    @property
    # AIDEV-NOTE: Computed property to check if the current step is the last step in the workflow.
    def is_last_step(self) -> Annotated[bool, Field(exclude=True)]:
        return (self.cursor.step + 1) == len(self.current_workflow.steps)

    @computed_field
    @property
    # AIDEV-NOTE: Computed property to check if the current step is the first step in the workflow.
    def is_first_step(self) -> Annotated[bool, Field(exclude=True)]:
        return self.cursor.step == 0

    @computed_field
    @property
    # AIDEV-NOTE: Computed property to check if the current workflow is the main workflow.
    def is_main(self) -> Annotated[bool, Field(exclude=True)]:
        return self.cursor.workflow == "main"

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        dump = super().model_dump(*args, **kwargs)
        execution_input: dict = dump.pop("execution_input")

        return dump | execution_input

    # AIDEV-NOTE: Retrieves historical inputs, labels, and state for the current execution scope.
    async def get_inputs(
        self, _limit: int = 50
    ) -> tuple[list[Any], list[str | None], dict[str, Any]]:
        if self.execution_input.execution is None:
            return [], [], {}

        inputs = []
        labels = []
        state = {}
        scope_id = self.current_scope_id

        transitions = await list_execution_inputs_data(
            execution_id=self.execution_input.execution.id,
            direction="asc",
            scope_id=scope_id,
        )  # type: ignore[not-callable]
        assert len(transitions) > 0, "No transitions found"

        for transition in transitions:
            inputs.append(transition.output)
            labels.append(transition.step_label)

        transitions = await list_execution_state_data(
            execution_id=self.execution_input.execution.id,
            direction="asc",
            scope_id=scope_id,
        )  # type: ignore[not-callable]
        for transition in transitions:
            state.update(transition.output)

        return inputs, labels, state

    # AIDEV-NOTE: Prepares the step context by loading inputs and retrieving historical data for expression evaluation.
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


# AIDEV-NOTE: Represents the outcome of executing a single task step.
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
