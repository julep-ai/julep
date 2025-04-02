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

/** Base System definition */
@discriminator("systemDefType")
model SystemDef {
    /** The discriminator that tells the system which type this is */
    systemDefType: string;

    /** Resource is the name of the resource to use */
    resource: resourceType;

    /** Operation is the name of the operation to perform */
    operation: operationType;

    /** Resource id (if applicable) */
    resource_id?: uuid;

    /** Sub-resource type (if applicable) */
    subresource?: subresourceType;

    /** The arguments to pre-apply to the system call */
    arguments?: Record<unknown>;
}