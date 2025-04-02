import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Create User System Definition */
model CreateUserSystemDef extends SystemDef {
    systemDefType: "CreateUserSystemDef";
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
    systemDefType: "UpdateUserSystemDef";
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
    systemDefType: "PatchUserSystemDef";
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
    systemDefType: "GetUserSystemDef";
    resource: "user";
    operation: "get";
    resource_id: uuid;
}

/** List Users System Definition */
model ListUsersSystemDef extends SystemDef {
    systemDefType: "ListUsersSystemDef";
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
    systemDefType: "DeleteUserSystemDef";
    resource: "user";
    operation: "delete";
    resource_id: uuid;
}