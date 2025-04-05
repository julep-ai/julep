import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Create User System Definition */
model CreateUserSystemDef extends SystemDef {
    system_def_type: "CreateUserSystemDef" = "CreateUserSystemDef";
    resource: "user";
    operation: "create";
    arguments: {
        user_id: string;
        name?: string;
        metadata?: Record<unknown>;
    };
}

/** Update User System Definition */
model UpdateUserSystemDef extends SystemDef {
    system_def_type: "UpdateUserSystemDef" = "UpdateUserSystemDef";
    resource: "user";
    operation: "update";
    resource_id: uuid;
    arguments: {
        user_id?: string;
        name?: string;
        metadata?: Record<unknown>;
    };
}

/** Patch User System Definition */
model PatchUserSystemDef extends SystemDef {
    system_def_type: "PatchUserSystemDef" = "PatchUserSystemDef";
    resource: "user";
    operation: "patch";
    resource_id: uuid;
    arguments: {
        name?: string;
        metadata?: Record<unknown>;
    };
}

/** Get User System Definition */
model GetUserSystemDef extends SystemDef {
    system_def_type: "GetUserSystemDef" = "GetUserSystemDef";
    resource: "user";
    operation: "get";
    resource_id: uuid;
}

/** List Users System Definition */
model ListUsersSystemDef extends SystemDef {
    system_def_type: "ListUsersSystemDef" = "ListUsersSystemDef";
    resource: "user";
    operation: "list";
    arguments?: {
        filter?: string;
        limit?: int32;
        offset?: int32;
    };
}

/** Delete User System Definition */
model DeleteUserSystemDef extends SystemDef {
    system_def_type: "DeleteUserSystemDef" = "DeleteUserSystemDef";
    resource: "user";
    operation: "delete";
    resource_id: uuid;
}