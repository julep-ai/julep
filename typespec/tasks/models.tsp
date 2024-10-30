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

    /**
     * Validates the workflow structure, ensuring that all referenced tools and steps are valid
     * and that the workflow is logically consistent.
     */
    @method
    validate(): void {
        // Implement workflow validation logic
    }
}

model TaskTool extends CreateToolRequest {
    /** Read-only: Whether the tool was inherited or not. Only applies within tasks. */
    @visibility("read")
    inherited?: boolean = false;
}

/** Reference to a tool by id */
model ToolRefById {
    @visibility("read", "create")
    @validatorFn(validateUUID)
    id?: uuid;
}

/** Reference to a tool by name */
model ToolRefByName {
    @visibility("read", "create")
    @validatorFn(validatePythonIdentifier)
    name?: validPythonIdentifier;
}

/** Reference to a tool */
model ToolRef {
    @visibility("read", "create")
    ref: ToolRefById | ToolRefByName;
}

/** Object describing a Task */
model Task {
    @visibility("read", "create")
    @validatorFn(validateTaskName)
    name: string;

    description: string = "";

    /** The entrypoint of the task. */
    @minItems(1)
    main: WorkflowStep[];

    /** The schema for the input to the task. `null` means all inputs are valid. */
    @validatorFn(validateInputSchema)
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
    @validatorFn(validateUUID)
    id: uuid;

    ...CreateTaskRequest;
}

/**
 * Orchestrates the execution of a workflow, handling the invocation of individual steps
 * and managing the data flow between them.
 */
class WorkflowExecutor {
    /**
     * Executes the given workflow asynchronously.
     * @param workflow The workflow to execute.
     * @returns A promise that resolves when the workflow execution is complete.
     */
    async executeWorkflow(workflow: Workflow): Promise<void> {
        // Implement workflow execution logic
    }
}

/**
 * Validates the given UUID.
 * @param value The value to validate.
 * @returns `true` if the value is a valid UUID, `false` otherwise.
 */
function validateUUID(value: unknown): boolean {
    // Implement UUID validation logic
}

/**
 * Validates the given Python identifier.
 * @param value The value to validate.
 * @returns `true` if the value is a valid Python identifier, `false` otherwise.
 */
function validatePythonIdentifier(value: unknown): boolean {
    // Implement Python identifier validation logic
}

/**
 * Validates the given task name.
 * @param value The value to validate.
 * @returns `true` if the value is a valid task name, `false` otherwise.
 */
function validateTaskName(value: unknown): boolean {
    // Implement task name validation logic
}

/**
 * Validates the given input schema.
 * @param value The value to validate.
 * @returns `true` if the value is a valid input schema, `false` otherwise.
 */
function validateInputSchema(value: unknown): boolean {
    // Implement input schema validation logic
}
