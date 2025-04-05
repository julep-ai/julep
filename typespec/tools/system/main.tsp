import "../../common";
import "./agents.tsp";
import "./docs.tsp";
import "./sessions.tsp";
import "./tasks.tsp";
import "./users.tsp";

using Common;

namespace Tools;

/** A valid resource type in the system */
alias resourceType = (
    | "agent"
    | "user"
    | "task"
    | "execution"
    | "doc"
    | "session"
    | "job"
);

/** A valid subresource type in the system */
alias subresourceType = (
    | "tool"
    | "doc"
    | "execution"
    | "transition"
);

/** A valid operation type in the system */
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

model SystemDefArguments extends Record<unknown> {}

/** Base System definition */
@discriminator("system_def_type")
model SystemDef {
    /** The discriminator that tells the system which type this is */
    system_def_type: string;

    /** Resource is the name of the resource to use */
    resource: resourceType;

    /** Operation is the name of the operation to perform */
    operation: operationType;

    /** Resource id (if applicable) */
    resource_id?: uuid;

    /** Sub-resource type (if applicable) */
    subresource?: subresourceType;

    /** The arguments to pre-apply to the system call */
    arguments?: SystemDefArguments;
}

/** Model for chosen system call arguments */
model SystemCallArguments {
    /** The arguments to pass to the system call */
    arguments: string; // JSON string of arguments
}

/** Model for the system call option in a tool call */
model ChosenSystemCallOption {
    /** The resource type to operate on */
    resource: resourceType;
    
    /** The operation to perform */
    operation: operationType;
    
    /** The resource id (if applicable) */
    resource_id?: uuid;
    
    /** The subresource type (if applicable) */
    subresource?: subresourceType;
    
    /** The arguments for the system call */
    arguments?: string; // May be a JSON string
}