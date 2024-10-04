import "../common";

import "../agents/models.tsp";
import "../docs/models.tsp";
import "../sessions/models.tsp";
import "../users/models.tsp";
import "../jobs/models.tsp";
import "../tasks/models.tsp";
import "../executions/models.tsp";

using Agents;
using Common;
using Docs;
using Sessions;
using Users;
using Jobs;
using Tasks;
using Executions;

namespace Tools;

//
// SYSTEM TOOL MODELS
//

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
    // | "chat"  // TODO: add chat operations
    | "history"
    | "delete"
    | "get"
    | "list"
);

/** Base system definition */
model BaseSystemDef {
    /** Resource is the name of the resource to use */
    resource: resourceType;

    /** Resource id (if applicable) */
    resource_id?: uuid;

    /** Sub-resource type (if applicable) */
    subresource?: uuid;

    /** Operation is the name of the operation to perform */
    operation: operationType;

    /** The arguments to pre-apply to the system call */
    arguments?: unknown;
}

// // In order to avoid circular dependency, we need to re-define the agent request models here
// model SystemCreateAgentRequest {
//     ...CreateAgentRequest;
// }

// model SystemUpdateAgentRequest {
//     ...UpdateAgentRequest;
// }

// model SystemPatchAgentRequest {
//     ...PatchAgentRequest;
// }

// model SystemCreateOrUpdateAgentRequest {
//     ...CreateOrUpdateAgentRequest;
// }

// model SystemAgentCreateDef extends BaseSystemDef {
//     resource: "agent" = "agent";
//     operation: "create" = "create";
//     resource_id?: never;
//     subresource?: never;
//     arguments: SystemCreateAgentRequest;
// }

// model SystemAgentUpdateDef extends BaseSystemDef {
//     resource: "agent" = "agent";
//     operation: "update" = "update";
//     resource_id: uuid;
//     subresource?: never;
//     arguments: SystemUpdateAgentRequest;
// }

model SystemAgentListDef extends BaseSystemDef {
    resource: "agent" = "agent";
    operation: "list" = "list";
    resource_id?: never;
    subresource?: never;
    arguments: PaginationOptions;
}

model SystemAgentDeleteDef extends BaseSystemDef {
    resource: "agent" = "agent";
    operation: "delete" = "delete";
    resource_id: uuid;
    subresource?: never;
    arguments?: never;
}

// model SystemAgentCreateOrUpdateDef extends BaseSystemDef {
//     resource: "agent" = "agent";
//     operation: "create_or_update" = "create_or_update";
//     resource_id?: never;
//     subresource?: never;
//     arguments: SystemCreateOrUpdateAgentRequest;
// }

model SystemAgentGetDef extends BaseSystemDef {
    resource: "agent" = "agent";
    operation: "get" = "get";
    resource_id: uuid;
    subresource?: never;
    arguments?: never;
}

// model SystemAgentPatchDef extends BaseSystemDef {
//     resource: "agent" = "agent";
//     operation: "patch" = "patch";
//     resource_id: uuid;
//     subresource?: never;
//     arguments: SystemPatchAgentRequest;
// }

// In order to avoid circular dependency, we need to re-define the tool request models here
model SystemCreateToolRequest {
    ...CreateToolRequest;
}

model SystemUpdateToolRequest {
    ...UpdateToolRequest;
}

model SystemPatchToolRequest {
    ...PatchToolRequest;
}

model SystemToolCreateDef extends BaseSystemDef {
    resource: "agent" = "agent";
    resource_id: uuid;
    subresource: "tool" = "tool";
    operation: "create" = "create";
    arguments: SystemCreateToolRequest;
}

model SystemToolUpdateDef extends BaseSystemDef {
    resource: "agent" = "agent";
    resource_id: uuid;
    subresource: "tool" = "tool";
    operation: "update" = "update";
    arguments: SystemUpdateToolRequest;
}

model SystemToolListDef extends BaseSystemDef {
    resource: "agent" = "agent";
    resource_id: uuid;
    subresource: "tool" = "tool";
    operation: "list" = "list";
    arguments: PaginationOptions;
}

model SystemToolDeleteDef extends BaseSystemDef {
    resource: "agent" = "agent";
    resource_id: uuid;
    subresource: "tool" = "tool";
    operation: "delete" = "delete";
    arguments?: never;
}

model SystemToolPatchDef extends BaseSystemDef {
    resource: "agent" = "agent";
    resource_id: uuid;
    subresource: "tool" = "tool";
    operation: "patch" = "patch";
    arguments: SystemPatchToolRequest;
}

model SystemDocCreateDef extends BaseSystemDef {
    resource: "agent" | "user" = "agent";
    resource_id: uuid;
    subresource: "doc" = "doc";
    operation: "create" = "create";
    arguments: CreateDocRequest;
}

model SystemDocListDef extends BaseSystemDef {
    resource: "agent" | "user" = "agent";
    resource_id: uuid;
    subresource: "doc" = "doc";
    operation: "list" = "list";
    arguments: PaginationOptions;
}

model SystemDocDeleteDef extends BaseSystemDef {
    resource: "agent" | "user" = "agent";
    resource_id: uuid;
    subresource: "doc" = "doc";
    operation: "delete" = "delete";
    arguments?: never;
}

model SystemDocSearchDef extends BaseSystemDef {
    resource: "agent" | "user" = "agent";
    resource_id: uuid;
    subresource: "doc" = "doc";
    operation: "search" = "search";
    arguments: DocSearchRequest;
}

model SystemDocGetDef extends BaseSystemDef {
    resource: "doc" = "doc";
    resource_id: uuid;
    subresource?: never;
    operation: "get" = "get";
    arguments?: never;
}

model SystemDocEmbedDef extends BaseSystemDef {
    resource: "doc" = "doc";
    resource_id?: never;
    subresource?: never;
    operation: "embed" = "embed";
    arguments: EmbedQueryRequest;
}

model SystemSessionCreateDef extends BaseSystemDef {
    resource: "session";
    resource_id: uuid;
    subresource?: never;
    operation: "create" = "create";
    arguments: CreateSessionRequest;
}

model SystemSessionUpdateDef extends BaseSystemDef {
    resource: "session";
    resource_id: uuid;
    subresource?: never;
    operation: "update" = "update";
    arguments: UpdateSessionRequest;
}

model SystemSessionListDef extends BaseSystemDef {
    resource: "session";
    resource_id: uuid;
    subresource?: never;
    operation: "list" = "list";
    arguments: PaginationOptions;
}

model SystemSessionDeleteDef extends BaseSystemDef {
    resource: "session";
    resource_id: uuid;
    subresource?: never;
    operation: "delete" = "delete";
    arguments?: never;
}

model SystemSessionCreateOrUpdateDef extends BaseSystemDef {
    resource: "session";
    resource_id: uuid;
    subresource?: never;
    operation: "create_or_update" = "create_or_update";
    arguments: CreateOrUpdateSessionRequest;
}

model SystemSessionGetDef extends BaseSystemDef {
    resource: "session";
    resource_id: uuid;
    subresource?: never;
    operation: "get" = "get";
    arguments?: never;
}

model SystemSessionHistoryDef extends BaseSystemDef {
    resource: "session";
    resource_id: uuid;
    subresource?: never;
    operation: "history" = "history";
    arguments?: never;
}

model SystemSessionPatchDef extends BaseSystemDef {
    resource: "session";
    resource_id: uuid;
    subresource?: never;
    operation: "patch" = "patch";
    arguments: PatchSessionRequest;
}

model SystemUserCreateDef extends BaseSystemDef {
    resource: "user";
    resource_id: uuid;
    subresource?: never;
    operation: "create" = "create";
    arguments: CreateUserRequest;
}

model SystemUserUpdateDef extends BaseSystemDef {
    resource: "user";
    resource_id: uuid;
    subresource?: never;
    operation: "update" = "update";
    arguments: UpdateUserRequest;
}

model SystemUserListDef extends BaseSystemDef {
    resource: "user";
    resource_id: uuid;
    subresource?: never;
    operation: "list" = "list";
    arguments: PaginationOptions;
}

model SystemUserDeleteDef extends BaseSystemDef {
    resource: "user";
    resource_id: uuid;
    subresource?: never;
    operation: "delete" = "delete";
    arguments?: never;
}

model SystemUserCreateOrUpdateDef extends BaseSystemDef {
    resource: "user";
    resource_id: uuid;
    subresource?: never;
    operation: "create_or_update" = "create_or_update";
    arguments: CreateOrUpdateUserRequest;
}

model SystemUserGetDef extends BaseSystemDef {
    resource: "user";
    resource_id: uuid;
    subresource?: never;
    operation: "get" = "get";
    arguments?: never;
}

model SystemUserPatchDef extends BaseSystemDef {
    resource: "user";
    resource_id: uuid;
    subresource?: never;
    operation: "patch" = "patch";
    arguments: PatchUserRequest;
}

model SystemJobGetDef extends BaseSystemDef {
    resource: "job";
    resource_id: uuid;
    subresource?: never;
    operation: "get" = "get";
    arguments?: never;
}

// model SystemTaskCreateDef extends BaseSystemDef {
//     resource: "agent";
//     resource_id: uuid;
//     subresource: "task" = "task";
//     operation: "create" = "create";
//     arguments: CreateTaskRequest;
// }

model SystemTaskListDef extends BaseSystemDef {
    resource: "agent";
    resource_id: uuid;
    subresource: "task" = "task";
    operation: "list" = "list";
    arguments: PaginationOptions;
}

model SystemTaskGetDef extends BaseSystemDef {
    resource: "task";
    resource_id: uuid;
    subresource?: never;
    operation: "get" = "get";
    arguments?: never;
}

model SystemExecutionCreateDef extends BaseSystemDef {
    resource: "task";
    resource_id: uuid;
    subresource: "execution" = "execution";
    operation: "create" = "create";
    arguments: CreateExecutionRequest;
}

model SystemExecutionListDef extends BaseSystemDef {
    resource: "task";
    resource_id: uuid;
    subresource: "execution" = "execution";
    operation: "list" = "list";
    arguments: PaginationOptions;
}

model SystemExecutionChangeStatusDef extends BaseSystemDef {
    resource: "execution";
    resource_id: uuid;
    subresource?: never;
    operation: "change_status" = "change_status";
    arguments: ResumeExecutionRequest | StopExecutionRequest;
}

model SystemExecutionGetDef extends BaseSystemDef {
    resource: "execution";
    resource_id: uuid;
    subresource?: never;
    operation: "get" = "get";
    arguments?: never;
}

model SystemTransitionListDef extends BaseSystemDef {
    resource: "execution";
    resource_id: uuid;
    subresource: "transition" = "transition";
    operation: "list" = "list";
    arguments: PaginationOptions;
}


alias SystemDef = (
    // | SystemAgentCreateDef   // TODO: add agent operations
    // | SystemAgentUpdateDef   // TODO: add agent operations
    | SystemAgentListDef
    | SystemAgentDeleteDef
    // | SystemAgentCreateOrUpdateDef   // TODO: add agent operations
    | SystemAgentGetDef
    // | SystemAgentPatchDef   // TODO: add agent operations
    | SystemToolCreateDef
    | SystemToolUpdateDef
    | SystemToolListDef
    | SystemToolDeleteDef
    | SystemToolPatchDef
    | SystemDocCreateDef
    | SystemDocListDef
    | SystemDocDeleteDef
    | SystemDocGetDef
    | SystemDocEmbedDef
    | SystemDocSearchDef
    | SystemSessionCreateDef
    | SystemSessionUpdateDef
    | SystemSessionListDef
    | SystemSessionDeleteDef
    | SystemSessionCreateOrUpdateDef
    | SystemSessionGetDef
    | SystemSessionHistoryDef
    | SystemSessionPatchDef
    | SystemUserCreateDef
    | SystemUserUpdateDef
    | SystemUserListDef
    | SystemUserDeleteDef
    | SystemUserCreateOrUpdateDef
    | SystemUserGetDef
    | SystemUserPatchDef
    | SystemJobGetDef
    // | SystemTaskCreateDef   // TODO: add task operations
    | SystemTaskListDef
    | SystemTaskGetDef
    | SystemExecutionCreateDef
    | SystemExecutionListDef
    | SystemExecutionChangeStatusDef
    | SystemExecutionGetDef
    | SystemTransitionListDef
);
