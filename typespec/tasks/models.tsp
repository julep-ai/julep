import "@typespec/http";

import "../common";
import "../tools";

import "./steps.tsp";

using TypeSpec.Http;

using Common;
using Tools;

namespace Tasks;

//
// TASK MODELS
//

model Workflow {
    @key name: validPythonIdentifier;

    /** The steps in the workflow */
    @minItems(1)
    steps: WorkflowStep[];
}

model TaskTool extends CreateToolRequest {
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
    @minItems(1)
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
