import "../agents";
import "../common";
import "../chat";
import "../entries";

using Agents;
using Chat;
using Common;
using Entries;

namespace Tasks;

//
// TASK MODELS
//

// -- cannot use an enum here coz typespec doesnt allow it in discriminated models
alias WorkflowStepKind = (
    /** A step that runs a tool */
    | "tool_call"

    /** A step that runs a subworkflow */
    | "yield"

    /** A step that runs a prompt */
    | "prompt"

    /** A step that evaluates an expression */
    | "evaluate"

    /** A step that runs a conditional */
    | "if_else"

    /** A step that runs a loop */
    | "loop"

    /** Throw an error */
    | "error"
);

@discriminator("__kind")
model WorkflowStep {
    @visibility("read")
    __kind?: WorkflowStepKind;
}

model ToolCallStep extends WorkflowStep {
    @visibility("read")
    __kind: "tool_call" = "tool_call";

    /** The tool to run */
    tool: toolType;

    /** The input parameters for the tool */
    arguments: Record<unknown>;
}

/** An object where values are strings in the Common Expression Language that get evaluated before being passed downstream */
scalar CEL extends string;
alias CELObject = Record<CEL>;

model YieldStep extends WorkflowStep {
    @visibility("read")
    __kind: "yield" = "yield";

    /** The subworkflow to run */
    workflow: string;

    /** The input parameters for the subworkflow */
    arguments: CELObject;
}

model PromptStep extends WorkflowStep {
    @visibility("read")
    __kind: "prompt" = "prompt";

    /** The prompt to run */
    prompt: string | InputChatMLMessage[];

    /** Settings for the prompt */
    settings: ChatSettings;
}

model EvaluateStep extends WorkflowStep {
    @visibility("read")
    __kind: "evaluate" = "evaluate";

    /** The expression to evaluate */
    evaluate: CELObject;
}

model IfElseWorkflowStep extends WorkflowStep {
    @visibility("read")
    __kind: "if_else" = "if_else";

    /** The condition to evaluate */
    `if`: CEL;

    /** The steps to run if the condition is true */
    then: YieldStep;

    /** The steps to run if the condition is false */
    `else`: YieldStep;
}

model ErrorWorkflowStep extends WorkflowStep {
    @visibility("read")
    __kind: "error" = "error";

    /** The error message */
    error: string;
}

@withVisibility("create")
model CreateWorkflowStep {
    ...WorkflowStep;
}

model Workflow {
    @key name: identifierSafeUnicode;

    /** The steps in the workflow */
    steps: WorkflowStep[];
}

/** Object describing a Task */
model Task {
    @visibility("read", "create")
    name: string;

    description: string = "";
    main: WorkflowStep[];
    input_schema: Record<unknown> | null = null;
    tools: toolType[];
    
    @visibility("read")
    agent_id: Agent.id;

    ...HasId;
    ...HasTimestamps;
    ...Record<WorkflowStep[]>;
}

/** Payload for updating a task */
@withVisibility("update")
model UpdateTaskRequest {
    ...Task;
}

/** Payload for patching a task */
model PatchTaskRequest is UpdateTaskRequest {}

/** Payload for creating a task */
@withVisibility("create")
model CreateTaskRequest {
    ...Task;
}

model CreateOrUpdateTaskRequest {
    id: uuid;
    ...CreateTaskRequest;
}