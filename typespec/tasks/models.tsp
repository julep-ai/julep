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
    @visibility(Lifecycle.Read)
    inherited?: boolean = false;
}

/** Reference to a tool by id */
model ToolRefById {
    @visibility(Lifecycle.Read, Lifecycle.Create)
    id?: string;
}

/** Reference to a tool by name */
model ToolRefByName {
    @visibility(Lifecycle.Read, Lifecycle.Create)
    name?: validPythonIdentifier;
}

/** Reference to a tool */
model ToolRef {
    @visibility(Lifecycle.Read, Lifecycle.Create)
    ref: ToolRefById | ToolRefByName;
}

/** Object describing a Task */
model Task {
    /** The name of the task. */
    @visibility(Lifecycle.Read, Lifecycle.Create, Lifecycle.Update)
    name: displayName;

    /** The canonical name of the task. */
    canonical_name?: canonicalName;

    /** The description of the task. */
    description: string = "";

    /** The entrypoint of the task. */
    @minItems(1)
    main: WorkflowStep[];

    /** The schema for the input to the task. `null` means all inputs are valid. */
    input_schema: Record<unknown> | null = null;

    /** Tools defined specifically for this task not included in the Agent itself. */
    tools: TaskTool[] = #[];

    /** Whether to inherit tools from the parent agent or not. Defaults to false. */
    inherit_tools: boolean = false;

    ...HasId;
    ...HasTimestamps;
    ...HasMetadata;
    ...Record<WorkflowStep[]>;
}

/** Payload for updating a task */
@withVisibility(Lifecycle.Update)
model UpdateTaskRequest {
    ...Task;
}

/** Payload for patching a task */
model PatchTaskRequest is UpdateTaskRequest;

/** Payload for creating a task */
@withVisibility(Lifecycle.Create)
model CreateTaskRequest {
    ...Task;
}

model CreateOrUpdateTaskRequest {
    @path
    id: uuid;

    ...CreateTaskRequest;
}
