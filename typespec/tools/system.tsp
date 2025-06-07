import "./base.tsp";

using Tools;

namespace Tools;

// AIDEV-NOTE: Detailed system call models extracted from models.tsp.

alias resourceType = (
    | "agent"
    | "user"
    | "task"
    | "execution"
    | "doc"
    | "session"
    | "job"
);

alias subresourceType = (
    | "tool"
    | "doc"
    | "execution"
    | "transition"
);

alias operationType = (
    | "create"
    | "update"
    | "patch"
    | "create_or_update"
    | "embed"
    | "change_status"
    | "search"
    | "chat"
    | "history"
    | "delete"
    | "get"
    | "list"
);

@discriminator("operation")
model BaseSystemCall {
    /** Resource is the name of the resource to use */
    resource: resourceType;

    /** Operation is the name of the operation to perform */
    operation: operationType;

    /** Resource id (if applicable) */
    resource_id?: uuid;

    /** Sub-resource type (if applicable) */
    subresource?: subresourceType;

    /** The arguments to pre-apply to the system call */
    arguments?: FunctionParameters;
}

model CreateSystemCall extends BaseSystemCall {
    operation: "create";
}

model UpdateSystemCall extends BaseSystemCall {
    operation: "update";
}

model PatchSystemCall extends BaseSystemCall {
    operation: "patch";
}

model CreateOrUpdateSystemCall extends BaseSystemCall {
    operation: "create_or_update";
}

model EmbedSystemCall extends BaseSystemCall {
    operation: "embed";
}

model ChangeStatusSystemCall extends BaseSystemCall {
    operation: "change_status";
}

model SearchSystemCall extends BaseSystemCall {
    operation: "search";
}

model ChatSystemCall extends BaseSystemCall {
    operation: "chat";
}

model HistorySystemCall extends BaseSystemCall {
    operation: "history";
}

model DeleteSystemCall extends BaseSystemCall {
    operation: "delete";
}

model GetSystemCall extends BaseSystemCall {
    operation: "get";
}

model ListSystemCall extends BaseSystemCall {
    operation: "list";
}

alias SystemDef = (
    | CreateSystemCall
    | UpdateSystemCall
    | PatchSystemCall
    | CreateOrUpdateSystemCall
    | EmbedSystemCall
    | ChangeStatusSystemCall
    | SearchSystemCall
    | ChatSystemCall
    | HistorySystemCall
    | DeleteSystemCall
    | GetSystemCall
    | ListSystemCall
);
