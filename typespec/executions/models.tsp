import "@typespec/http";

import "../common";
import "../tasks";

using TypeSpec.Http;

using Common;
using Tasks;

namespace Executions;

//
// EXECUTION MODELS
//

/** The status of an execution */
alias ExecutionStatus = (
    /** The execution is queued and waiting to start */
    | "queued"

    /** The execution is starting */
    | "starting"

    /** The execution is running */
    | "running"

    /** The execution is awaiting input */
    | "awaiting_input"

    /** The execution has succeeded */
    | "succeeded"

    /** The execution has failed */
    | "failed"

    /** The execution has been cancelled by the user */
    | "cancelled"
);

model Execution {
    /** The ID of the task that the execution is running */
    @visibility("read")
    task_id: Task.id;

    /** The status of the execution */
    @visibility("read")
    status: ExecutionStatus;

    /** The input to the execution */
    input: Record<unknown>;

    /** The output of the execution if it succeeded */
    output?: unknown;

    /** The error of the execution if it failed */
    error?: string;

    ...HasTimestamps;
    ...HasMetadata;
    ...HasId;
}

/** Payload for creating an execution */
@withVisibility("create")
model CreateExecutionRequest {
    ...Execution;
}

@discriminator("status")
model UpdateExecutionRequest {
    status: ExecutionStatus;
}

model StopExecutionRequest extends UpdateExecutionRequest {
    status: "cancelled" = "cancelled";

    /** The reason for stopping the execution */
    reason: string | null = null;
}

model ResumeExecutionRequest extends UpdateExecutionRequest {
    status: "running" = "running";

    /** The input to resume the execution with */
    input?: Record<unknown>;
}

model TaskTokenResumeExecutionRequest {
    status: "running" = "running";

    /** A Task Token is a unique identifier for a specific Task Execution. */
    @query
    task_token: string;

    /** The input to resume the execution with */
    input?: Record<unknown>;
}

/*
- finish
- wait
- error
- step
- cancelled
*/

alias TransitionType = (
    | "init"
    | "branch_init"
    | "finish"
    | "finish_branch"
    | "wait"
    | "resume"
    | "error"
    | "step"
    | "cancelled"
);

model TransitionTarget {
    workflow: identifierSafeUnicode;
    step: uint16;
}

model TransitionEvent {
    @visibility("read")
    type: TransitionType;

    @visibility("read")
    output: unknown;

    ...HasTimestamps;
}

model Transition extends TransitionEvent {
    @visibility("read")
    execution_id: Execution.id;

    @visibility("read")
    current: TransitionTarget;

    @visibility("read")
    next: TransitionTarget | null;

    ...HasId;
    ...HasMetadata;
}