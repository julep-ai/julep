import "@typespec/http";

import "../agents";
import "../common";
import "../chat";
import "../entries";
import "../tools";

using TypeSpec.Http;

using Agents;
using Chat;
using Common;
using Entries;
using Tools;

namespace Tasks;

//
// TASK MODELS
//

alias WorkflowStepKind =
    | /** A step that runs a tool */
      "tool_call"
    | /** A step that runs a subworkflow */
      "yield"
    | /** A step that runs a prompt */
      "prompt"
    | /** A step that evaluates an expression */
      "evaluate"
    | /** A step that runs a conditional */
      "if_else"
    | /** A step that signals that it needs more input before resuming */
      "wait_for_input"
    | /** Throw an error */
      "error";

model BaseWorkflowStep {
    /** The kind of step */
    kind_: WorkflowStepKind;
}

model ToolCallStep extends BaseWorkflowStep {
    kind_: "tool_call" = "tool_call";

    /** The tool to run */
    tool: toolRef;

    /** The input parameters for the tool */
    arguments: Record<unknown>;
}

/** An object where values are strings in the Common Expression Language that get evaluated before being passed downstream */
alias ExpressionObject = Record<PyExpression>;

model YieldStep extends BaseWorkflowStep {
    kind_: "yield" = "yield";

    /** The subworkflow to run */
    workflow: string;

    /** The input parameters for the subworkflow */
    arguments: ExpressionObject;
}

model PromptStep extends BaseWorkflowStep {
    kind_: "prompt" = "prompt";

    /** The prompt to run */
    prompt: string | InputChatMLMessage[];

    /** Settings for the prompt */
    settings: ChatSettings;
}

model EvaluateStep extends BaseWorkflowStep {
    kind_: "evaluate" = "evaluate";

    /** The expression to evaluate */
    evaluate: ExpressionObject;
}

model ErrorWorkflowStep extends BaseWorkflowStep {
    kind_: "error" = "error";

    /** The error message */
    error: string;
}

model WaitForInputStep extends BaseWorkflowStep {
    kind_: "wait_for_input" = "wait_for_input";

    /** Any additional info or data */
    info: string | Record<unknown>;
}

alias NonConditionalWorkflowStep =
    | EvaluateStep
    | ToolCallStep
    | YieldStep
    | PromptStep
    | ErrorWorkflowStep
    | WaitForInputStep;

model IfElseWorkflowStep extends BaseWorkflowStep {
    kind_: "if_else" = "if_else";

    /** The condition to evaluate */
    `if`: PyExpression;

    /** The steps to run if the condition is true */
    then: NonConditionalWorkflowStep;

    /** The steps to run if the condition is false */
    `else`: NonConditionalWorkflowStep;
}

alias WorkflowStep = NonConditionalWorkflowStep | IfElseWorkflowStep;
alias CreateWorkflowStep = WorkflowStep;

model Workflow {
    @key name: validPythonIdentifier;

    /** The steps in the workflow */
    steps: WorkflowStep[];
}

model TaskTool extends CreateToolRequest{
    /** Read-only: Whether the tool was inherited or not. Only applies within tasks. */
    @visibility("read")
    inherited?: boolean = false;
}

/** Object describing a Task */
model Task {
    @visibility("read", "create")
    name: string;

    description: string = "";

    /** The entrypoint of the task. */
    main: WorkflowStep[];

    /** The schema for the input to the task. `null` means all inputs are valid. */
    input_schema: Record<unknown> | null = null;

    /** Tools defined specifically for this task not included in the Agent itself. */
    tools: TaskTool[] = #[];

    /** Whether to inherit tools from the parent agent or not. Defaults to true. */
    inherit_tools: boolean = true;

    ...HasId;
    ...HasTimestamps;
    ...HasMetadata;
    ...Record<WorkflowStep[]>;
}

/** Payload for updating a task */
@withVisibility("update")
model UpdateTaskRequest {
    ...Task;
}

/** Payload for patching a task */
model PatchTaskRequest is UpdateTaskRequest;

/** Payload for creating a task */
@withVisibility("create")
model CreateTaskRequest {
    ...Task;
}

model CreateOrUpdateTaskRequest {
    @path
    id: uuid;

    ...CreateTaskRequest;
}
