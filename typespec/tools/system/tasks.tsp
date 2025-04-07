import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Create Task System Definition Arguments */
model CreateTaskSystemDefArguments {
    /** Name of the task */
    name: string;
    
    /** Optional description for the task */
    description?: string;
    
    /** Steps that define the task workflow */
    steps: unknown[];
    
    /** Optional metadata for the task */
    metadata?: Record<unknown>;
}

/** Create Task System Definition */
model CreateTaskSystemDef extends SystemDef {
    system_def_type: "CreateTaskSystemDef" = "CreateTaskSystemDef";
    resource: "task";
    operation: "create";
    arguments?: CreateTaskSystemDefArguments;
}

/** Update Task System Definition Arguments */
model UpdateTaskSystemDefArguments {
    /** The task ID to update */
    resource_id: uuid;
    
    /** Optional name for the task */
    name?: string;
    
    /** Optional description for the task */
    description?: string;
    
    /** Optional steps that define the task workflow */
    steps?: unknown[];
    
    /** Optional metadata for the task */
    metadata?: Record<unknown>;
}

/** Update Task System Definition */
model UpdateTaskSystemDef extends SystemDef {
    system_def_type: "UpdateTaskSystemDef" = "UpdateTaskSystemDef";
    resource: "task";
    operation: "update";
    arguments?: UpdateTaskSystemDefArguments;
}

/** Patch Task System Definition Arguments */
model PatchTaskSystemDefArguments {
    /** The task ID to patch */
    resource_id: uuid;
    
    /** Optional name for the task */
    name?: string;
    
    /** Optional description for the task */
    description?: string;
    
    /** Optional metadata for the task */
    metadata?: Record<unknown>;
}

/** Patch Task System Definition */
model PatchTaskSystemDef extends SystemDef {
    system_def_type: "PatchTaskSystemDef" = "PatchTaskSystemDef";
    resource: "task";
    operation: "patch";
    arguments?: PatchTaskSystemDefArguments;
}

/** Get Task System Definition Arguments */
model GetTaskSystemDefArguments {
    /** The task ID to get */
    resource_id: uuid;
}

/** Get Task System Definition */
model GetTaskSystemDef extends SystemDef {
    system_def_type: "GetTaskSystemDef" = "GetTaskSystemDef";
    resource: "task";
    operation: "get";
    arguments?: GetTaskSystemDefArguments;
}

/** List Tasks System Definition Arguments */
model ListTasksSystemDefArguments {
    /** Filter string */
    filter?: string;
    
    /** Maximum number of results */
    limit?: int32;
    
    /** Offset for pagination */
    offset?: int32;
}

/** List Tasks System Definition */
model ListTasksSystemDef extends SystemDef {
    system_def_type: "ListTasksSystemDef" = "ListTasksSystemDef";
    resource: "task";
    operation: "list";
    arguments?: ListTasksSystemDefArguments;
}

/** Delete Task System Definition Arguments */
model DeleteTaskSystemDefArguments {
    /** The task ID to delete */
    resource_id: uuid;
}

/** Delete Task System Definition */
model DeleteTaskSystemDef extends SystemDef {
    system_def_type: "DeleteTaskSystemDef" = "DeleteTaskSystemDef";
    resource: "task";
    operation: "delete";
    arguments?: DeleteTaskSystemDefArguments;
}

/** Create Task Execution System Definition Arguments */
model CreateTaskExecutionSystemDefArguments {
    /** The task ID to execute */
    resource_id: uuid;
    
    /** Optional input data for the task execution */
    input?: unknown;
    
    /** Whether to execute the task asynchronously */
    async?: boolean;
}

/** Create Task Execution System Definition */
model CreateTaskExecutionSystemDef extends SystemDef {
    system_def_type: "CreateTaskExecutionSystemDef" = "CreateTaskExecutionSystemDef";
    resource: "task";
    operation: "create";
    subresource: "execution";
    arguments?: CreateTaskExecutionSystemDefArguments;
}

/** Get Task Execution System Definition Arguments */
model GetTaskExecutionSystemDefArguments {
    /** The execution ID to get */
    resource_id: uuid;
}

/** Get Task Execution System Definition */
model GetTaskExecutionSystemDef extends SystemDef {
    system_def_type: "GetTaskExecutionSystemDef" = "GetTaskExecutionSystemDef";
    resource: "execution";
    operation: "get";
    arguments?: GetTaskExecutionSystemDefArguments;
}