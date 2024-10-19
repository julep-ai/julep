# ruff: noqa: F401, F403, F405
import ast
from typing import (
    Annotated,
    Any,
    Generic,
    Literal,
    Self,
    Type,
    TypeVar,
    Union,
    get_args,
)
from uuid import UUID

import jinja2
from litellm.utils import _select_tokenizer as select_tokenizer
from litellm.utils import token_counter
from pydantic import (
    AwareDatetime,
    Field,
    ValidationError,
    computed_field,
    field_validator,
    model_validator,
)

from ..common.utils.datetime import utcnow
from .Agents import *
from .Chat import *
from .Common import *
from .Docs import *
from .Entries import *
from .Executions import *
from .Jobs import *
from .Sessions import *
from .Tasks import *
from .Tools import *
from .Users import *

# Generic models
# --------------

DataT = TypeVar("DataT", bound=BaseModel)


class ListResponse(BaseModel, Generic[DataT]):
    items: list[DataT]


# Aliases
# -------


class CreateToolRequest(UpdateToolRequest):
    pass


class CreateOrUpdateAgentRequest(UpdateAgentRequest):
    pass


class CreateOrUpdateUserRequest(UpdateUserRequest):
    pass


class CreateOrUpdateSessionRequest(CreateSessionRequest):
    pass


ChatResponse = ChunkChatResponse | MessageChatResponse


class MapReduceStep(Main):
    pass


class ChatMLTextContentPart(Content):
    pass


class ChatMLImageContentPart(ContentModel):
    pass


class InputChatMLMessage(Message):
    pass


# Patches
# -------


def type_property(self: BaseModel) -> str:
    return (
        "function"
        if self.function
        else "integration"
        if self.integration
        else "system"
        if self.system
        else "api_call"
        if self.api_call
        else None
    )


# Patch original Tool class to add 'type' property
TaskTool.type = computed_field(property(type_property))

# Patch original Tool class to add 'type' property
Tool.type = computed_field(property(type_property))

# Patch original UpdateToolRequest class to add 'type' property
UpdateToolRequest.type = computed_field(property(type_property))

# Patch original PatchToolRequest class to add 'type' property
PatchToolRequest.type = computed_field(property(type_property))


# Patch Task Workflow Steps
# -------------------------


def validate_python_expression(expr: str) -> tuple[bool, str]:
    try:
        ast.parse(expr)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError in '{expr}': {str(e)}"


def validate_jinja_template(template: str) -> tuple[bool, str]:
    env = jinja2.Environment()
    try:
        parsed_template = env.parse(template)
        for node in parsed_template.body:
            if isinstance(node, jinja2.nodes.Output):
                for child in node.nodes:
                    if isinstance(child, jinja2.nodes.Name):
                        # Check if the variable is a valid Python expression
                        is_valid, error = validate_python_expression(child.name)
                        if not is_valid:
                            return (
                                False,
                                f"Invalid Python expression in Jinja template '{template}': {error}",
                            )
        return True, ""
    except jinja2.exceptions.TemplateSyntaxError as e:
        return False, f"TemplateSyntaxError in '{template}': {str(e)}"


@field_validator("evaluate")
def validate_evaluate_expressions(cls, v):
    for key, expr in v.items():
        is_valid, error = validate_python_expression(expr)
        if not is_valid:
            raise ValueError(f"Invalid Python expression in key '{key}': {error}")
    return v


EvaluateStep.validate_evaluate_expressions = validate_evaluate_expressions


@field_validator("arguments")
def validate_arguments(cls, v):
    if isinstance(v, dict):
        for key, expr in v.items():
            if isinstance(expr, str):
                is_valid, error = validate_python_expression(expr)
                if not is_valid:
                    raise ValueError(
                        f"Invalid Python expression in arguments key '{key}': {error}"
                    )
    return v


ToolCallStep.validate_arguments = validate_arguments


# Add the new validator function
@field_validator("prompt")
def validate_prompt(cls, v):
    if isinstance(v, str):
        is_valid, error = validate_jinja_template(v)
        if not is_valid:
            raise ValueError(f"Invalid Jinja template in prompt: {error}")
    elif isinstance(v, list):
        for item in v:
            if "content" in item:
                is_valid, error = validate_jinja_template(item["content"])
                if not is_valid:
                    raise ValueError(
                        f"Invalid Jinja template in prompt content: {error}"
                    )
    return v


# Patch the original PromptStep class to add the new validator
PromptStep.validate_prompt = validate_prompt


@field_validator("set")
def validate_set_expressions(cls, v):
    for key, expr in v.items():
        is_valid, error = validate_python_expression(expr)
        if not is_valid:
            raise ValueError(f"Invalid Python expression in set key '{key}': {error}")
    return v


SetStep.validate_set_expressions = validate_set_expressions


@field_validator("log")
def validate_log_template(cls, v):
    is_valid, error = validate_jinja_template(v)
    if not is_valid:
        raise ValueError(f"Invalid Jinja template in log: {error}")
    return v


LogStep.validate_log_template = validate_log_template


@field_validator("return_")
def validate_return_expressions(cls, v):
    for key, expr in v.items():
        is_valid, error = validate_python_expression(expr)
        if not is_valid:
            raise ValueError(
                f"Invalid Python expression in return key '{key}': {error}"
            )
    return v


ReturnStep.validate_return_expressions = validate_return_expressions


@field_validator("arguments")
def validate_yield_arguments(cls, v):
    if isinstance(v, dict):
        for key, expr in v.items():
            is_valid, error = validate_python_expression(expr)
            if not is_valid:
                raise ValueError(
                    f"Invalid Python expression in yield arguments key '{key}': {error}"
                )
    return v


YieldStep.validate_yield_arguments = validate_yield_arguments


@field_validator("if_")
def validate_if_expression(cls, v):
    is_valid, error = validate_python_expression(v)
    if not is_valid:
        raise ValueError(f"Invalid Python expression in if condition: {error}")
    return v


IfElseWorkflowStep.validate_if_expression = validate_if_expression


@field_validator("over")
def validate_over_expression(cls, v):
    is_valid, error = validate_python_expression(v)
    if not is_valid:
        raise ValueError(f"Invalid Python expression in over: {error}")
    return v


@field_validator("reduce")
def validate_reduce_expression(cls, v):
    if v is not None:
        is_valid, error = validate_python_expression(v)
        if not is_valid:
            raise ValueError(f"Invalid Python expression in reduce: {error}")
    return v


MapReduceStep.validate_over_expression = validate_over_expression
MapReduceStep.validate_reduce_expression = validate_reduce_expression


# Patch workflow
# --------------

_CreateTaskRequest = CreateTaskRequest

CreateTaskRequest.model_config = ConfigDict(
    **{
        **_CreateTaskRequest.model_config,
        "extra": "allow",
    }
)


@model_validator(mode="before")
def validate_task_request(self):
    workflows = {
        k: v
        for k, v in self.model_dump().items()
        if k not in _CreateTaskRequest.model_fields or k == "main"
    }

    for workflow_name, workflow_definition in workflows.items():
        try:
            validate_workflow_steps(workflow_definition)
            setattr(self, workflow_name, WorkflowType(workflow_definition))
        except ValueError as e:
            raise ValueError(f"Invalid workflow '{
                             workflow_name}': {str(e)}")
    return self


CreateTaskRequest.validate_task_request = validate_task_request


def validate_workflow_steps(steps):
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or len(step) != 1:
            raise ValueError(f"Invalid step format at index {index}")

        step_type, step_content = next(iter(step.items()))
        try:
            validate_step(step_type, step_content, index)
        except ValueError as e:
            raise ValueError(f"Error in step {index}: {str(e)}")


def validate_evaluate_step(content):
    if not isinstance(content, dict):
        raise ValueError("'evaluate' step content must be a dictionary")
    for key, value in content.items():
        if not isinstance(value, str):
            raise ValueError(f"In 'evaluate' step, the value for key '{
                             key}' must be a string (Python expression)")


def validate_prompt_step(content):
    if isinstance(content, str):
        is_valid, error = validate_jinja_template(content)
        if not is_valid:
            raise ValueError(f"Invalid Jinja template in prompt: {error}")
    elif isinstance(content, list):
        for item in content:
            if (
                not isinstance(item, dict)
                or "role" not in item
                or "content" not in item
            ):
                raise ValueError(
                    "Each prompt message must be a dictionary with 'role' and 'content' keys"
                )
            is_valid, error = validate_jinja_template(item["content"])
            if not is_valid:
                raise ValueError(f"Invalid Jinja template in prompt content: {error}")
    else:
        raise ValueError("Prompt content must be either a string or a list of messages")


def validate_tool_call_step(content):
    if not isinstance(content, dict):
        raise ValueError("'tool' step content must be a dictionary")
    if "tool" not in content:
        raise ValueError("'tool' step must contain a 'tool' key with the tool name")
    if "arguments" in content:
        if not isinstance(content["arguments"], dict):
            raise ValueError("'arguments' in tool call step must be a dictionary")
        for key, value in content["arguments"].items():
            if isinstance(value, str):
                is_valid, error = validate_python_expression(value)
                if not is_valid:
                    raise ValueError(
                        f"Invalid Python expression in tool argument '{key}': {error}"
                    )


def validate_get_step(content):
    if not isinstance(content, dict):
        raise ValueError("'get' step content must be a dictionary")
    for key, value in content.items():
        if not isinstance(value, str):
            raise ValueError(f"In 'get' step, the value for key '{
                             key}' must be a string (variable name)")


def validate_set_step(content):
    if not isinstance(content, dict):
        raise ValueError("'set' step content must be a dictionary")
    for key, value in content.items():
        is_valid, error = validate_python_expression(value)
        if not is_valid:
            raise ValueError(
                f"Invalid Python expression in 'set' step for key '{key}': {error}"
            )


def validate_sleep_step(content):
    if not isinstance(content, (int, float)) or content < 0:
        raise ValueError("'sleep' step content must be a non-negative number")


def validate_yield_step(content):
    if not isinstance(content, dict):
        raise ValueError("'yield' step content must be a dictionary")
    if "workflow" not in content:
        raise ValueError(
            "'yield' step must contain a 'workflow' key with the workflow name"
        )
    if "arguments" in content:
        if not isinstance(content["arguments"], dict):
            raise ValueError("'arguments' in yield step must be a dictionary")
        for key, value in content["arguments"].items():
            is_valid, error = validate_python_expression(value)
            if not is_valid:
                raise ValueError(
                    f"Invalid Python expression in yield argument '{key}': {error}"
                )


def validate_if_else_step(content):
    if not isinstance(content, dict):
        raise ValueError("'if' step content must be a dictionary")
    if "if" not in content:
        raise ValueError("'if' step must contain an 'if' key with the condition")
    if "then" not in content:
        raise ValueError(
            "'if' step must contain a 'then' key with the steps to execute if condition is true"
        )

    is_valid, error = validate_python_expression(content["if"])
    if not is_valid:
        raise ValueError(f"Invalid Python expression in 'if' condition: {error}")

    validate_workflow_steps(content["then"])

    if "else" in content:
        validate_workflow_steps(content["else"])


def validate_switch_step(content, index, workflow_name):
    if not isinstance(content, list):
        raise ValueError("'switch' step content must be a list of case-then pairs")
    for case_index, case in enumerate(content):
        if not isinstance(case, dict) or "case" not in case or "then" not in case:
            raise ValueError(
                f"Each case in 'switch' step must be a dictionary with 'case' and 'then' keys"
            )
        if case["case"] != "_":
            is_valid, error = validate_python_expression(case["case"])
            if not is_valid:
                raise ValueError(f"Invalid Python expression in 'switch' case {
                                 case_index}: {error}")
        validate_workflow_steps([case["then"]])


def validate_foreach_step(content, index, workflow_name):
    if not isinstance(content, dict):
        raise ValueError("'foreach' step content must be a dictionary")
    if "in" not in content:
        raise ValueError("'foreach' step must contain an 'in' key with the iterable")
    if "do" not in content:
        raise ValueError(
            "'foreach' step must contain a 'do' key with the steps to execute for each iteration"
        )

    is_valid, error = validate_python_expression(content["in"])
    if not is_valid:
        raise ValueError(f"Invalid Python expression in 'foreach' iterable: {error}")

    validate_workflow_steps([content["do"]])


def validate_parallel_step(content, index, workflow_name):
    if not isinstance(content, list):
        raise ValueError(
            "'parallel' step content must be a list of steps to execute in parallel"
        )
    for parallel_index, parallel_step in enumerate(content):
        validate_workflow_steps(
            [parallel_step], f"{workflow_name}.parallel{parallel_index}"
        )


def validate_map_reduce_step(content):
    if not isinstance(content, dict):
        raise ValueError("'map_reduce' step content must be a dictionary")
    if "over" not in content:
        raise ValueError(
            "'map_reduce' step must contain an 'over' key with the iterable"
        )
    if "map" not in content:
        raise ValueError(
            "'map_reduce' step must contain a 'map' key with the mapping function"
        )

    is_valid, error = validate_python_expression(content["over"])
    if not is_valid:
        raise ValueError(f"Invalid Python expression in 'map_reduce' iterable: {error}")

    validate_workflow_steps([content["map"]], f"{workflow_name}.map")

    if "reduce" in content:
        is_valid, error = validate_python_expression(content["reduce"])
        if not is_valid:
            raise ValueError(
                f"Invalid Python expression in 'map_reduce' reduce function: {error}"
            )


# Update the step_validators dictionary
step_validators = {
    "evaluate": validate_evaluate_step,
    "prompt": validate_prompt_step,
    "tool": validate_tool_call_step,
    "get": validate_get_step,
    "set": validate_set_step,
    "log": validate_log_template,  # This function is already defined
    "return": validate_return_expressions,  # This function is already defined
    "sleep": validate_sleep_step,
    # No additional validation needed for error step
    "error": lambda content, index, workflow_name: None,
    "yield": validate_yield_step,
    "if": validate_if_else_step,
    "switch": validate_switch_step,
    "foreach": validate_foreach_step,
    "parallel": validate_parallel_step,
    "map_reduce": validate_map_reduce_step,
}


def validate_step(step_type, step_content):
    validator = step_validators.get(step_type)
    if validator:
        validator(step_content)
    else:
        raise ValueError(f"Unknown step type '{step_type}'")


# Custom types (not generated correctly)
# --------------------------------------

ChatMLContent = (
    list[ChatMLTextContentPart | ChatMLImageContentPart]
    | Tool
    | ChosenToolCall
    | str
    | ToolResponse
    | list[
        list[ChatMLTextContentPart | ChatMLImageContentPart]
        | Tool
        | ChosenToolCall
        | str
        | ToolResponse
    ]
)

# Extract ChatMLRole
ChatMLRole = BaseEntry.model_fields["role"].annotation

# Extract ChatMLSource
ChatMLSource = BaseEntry.model_fields["source"].annotation

# Extract ExecutionStatus
ExecutionStatus = Execution.model_fields["status"].annotation

# Extract TransitionType
TransitionType = Transition.model_fields["type"].annotation

# Assertions to ensure consistency (optional, but recommended for runtime checks)
assert ChatMLRole == BaseEntry.model_fields["role"].annotation
assert ChatMLSource == BaseEntry.model_fields["source"].annotation
assert ExecutionStatus == Execution.model_fields["status"].annotation
assert TransitionType == Transition.model_fields["type"].annotation


# Create models
# -------------


class CreateTransitionRequest(Transition):
    # The following fields are optional in this

    id: UUID | None = None
    execution_id: UUID | None = None
    created_at: AwareDatetime | None = None
    updated_at: AwareDatetime | None = None
    metadata: dict[str, Any] | None = None
    task_token: str | None = None


class CreateEntryRequest(BaseEntry):
    timestamp: Annotated[
        float, Field(ge=0.0, default_factory=lambda: utcnow().timestamp())
    ]

    @classmethod
    def from_model_input(
        cls: Type[Self],
        model: str,
        *,
        role: ChatMLRole,
        content: ChatMLContent,
        name: str | None = None,
        source: ChatMLSource,
        **kwargs: dict,
    ) -> Self:
        tokenizer: dict = select_tokenizer(model=model)
        token_count = token_counter(
            model=model, messages=[{"role": role, "content": content, "name": name}]
        )

        return cls(
            role=role,
            content=content,
            name=name,
            source=source,
            tokenizer=tokenizer["type"],
            token_count=token_count,
            **kwargs,
        )


# Workflow related models
# -----------------------

WorkflowStep = (
    EvaluateStep
    | ToolCallStep
    | PromptStep
    | GetStep
    | SetStep
    | LogStep
    | ReturnStep
    | SleepStep
    | ErrorWorkflowStep
    | YieldStep
    | WaitForInputStep
    | IfElseWorkflowStep
    | SwitchStep
    | ForeachStep
    | ParallelStep
    | MapReduceStep
)


class Workflow(BaseModel):
    name: str
    steps: list[WorkflowStep]


# Task spec helper models
# ----------------------


class TaskToolDef(BaseModel):
    type: str
    name: str
    spec: dict
    inherited: bool = False


_Task = Task


class TaskSpec(_Task):
    model_config = ConfigDict(extra="ignore")

    workflows: list[Workflow]
    tools: list[TaskToolDef]

    # Remove main field from the model
    main: None = None


class TaskSpecDef(TaskSpec):
    id: UUID | None = None
    created_at: AwareDatetime | None = None
    updated_at: AwareDatetime | None = None


class PartialTaskSpecDef(TaskSpecDef):
    name: str | None = None


class Task(_Task):
    model_config = ConfigDict(
        **{
            **_Task.model_config,
            "extra": "allow",
        }
    )


# Patch some models to allow extra fields
# --------------------------------------

WorkflowType = RootModel[
    list[
        EvaluateStep
        | ToolCallStep
        | PromptStep
        | GetStep
        | SetStep
        | LogStep
        | ReturnStep
        | SleepStep
        | ErrorWorkflowStep
        | YieldStep
        | WaitForInputStep
        | IfElseWorkflowStep
        | SwitchStep
        | ForeachStep
        | ParallelStep
        | MapReduceStep
    ]
]


CreateOrUpdateTaskRequest = CreateTaskRequest

_PatchTaskRequest = PatchTaskRequest


class PatchTaskRequest(_PatchTaskRequest):
    model_config = ConfigDict(
        **{
            **_PatchTaskRequest.model_config,
            "extra": "allow",
        }
    )


_UpdateTaskRequest = UpdateTaskRequest


class UpdateTaskRequest(_UpdateTaskRequest):
    model_config = ConfigDict(
        **{
            **_UpdateTaskRequest.model_config,
            "extra": "allow",
        }
    )
