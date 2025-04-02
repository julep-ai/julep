import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Create Task System Definition */
model CreateTaskSystemDef extends SystemDef {
    systemDefType: "CreateTaskSystemDef";
    resource: "task";
    operation: "create";
    arguments: {
        name: string;
        description?: string;
        steps: unknown[];
        metadata?: Record<unknown>;
    };
}

/** Update Task System Definition */
model UpdateTaskSystemDef extends SystemDef {
    systemDefType: "UpdateTaskSystemDef";
    resource: "task";
    operation: "update";
    resource_id: uuid;
    arguments: {
        name?: string;
        description?: string;
        steps?: unknown[];
        metadata?: Record<unknown>;
    };
}

/** Patch Task System Definition */
model PatchTaskSystemDef extends SystemDef {
    systemDefType: "PatchTaskSystemDef";
    resource: "task";
    operation: "patch";
    resource_id: uuid;
    arguments: {
        name?: string;
        description?: string;
        metadata?: Record<unknown>;
    };
}

/** Get Task System Definition */
model GetTaskSystemDef extends SystemDef {
    systemDefType: "GetTaskSystemDef";
    resource: "task";
    operation: "get";
    resource_id: uuid;
}

/** List Tasks System Definition */
model ListTasksSystemDef extends SystemDef {
    systemDefType: "ListTasksSystemDef";
    resource: "task";
    operation: "list";
    arguments?: {
        filter?: string;
        limit?: int32;
        offset?: int32;
    };
}

/** Delete Task System Definition */
model DeleteTaskSystemDef extends SystemDef {
    systemDefType: "DeleteTaskSystemDef";
    resource: "task";
    operation: "delete";
    resource_id: uuid;
}

/** Create Task Execution System Definition */
model CreateTaskExecutionSystemDef extends SystemDef {
    systemDefType: "CreateTaskExecutionSystemDef";
    resource: "task";
    operation: "create";
    resource_id: uuid;
    subresource: "execution";
    arguments?: {
        input?: unknown;
        async?: boolean;
    };
}

/** Get Task Execution System Definition */
model GetTaskExecutionSystemDef extends SystemDef {
    systemDefType: "GetTaskExecutionSystemDef";
    resource: "execution";
    operation: "get";
    resource_id: uuid;
}