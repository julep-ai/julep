import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Create User System Definition Arguments */
model CreateUserSystemDefArguments {
    /** User identifier */
    user_id: string;
    
    /** Optional name for the user */
    name?: string;
    
    /** Optional metadata for the user */
    metadata?: Record<unknown>;
}

/** Create User System Definition */
model CreateUserSystemDef extends SystemDef {
    system_def_type: "CreateUserSystemDef" = "CreateUserSystemDef";
    resource: "user";
    operation: "create";
    arguments?: CreateUserSystemDefArguments;
}

/** Update User System Definition Arguments */
model UpdateUserSystemDefArguments {
    /** The user ID to update */
    resource_id: uuid;
    
    /** Optional user identifier */
    user_id?: string;
    
    /** Optional name for the user */
    name?: string;
    
    /** Optional metadata for the user */
    metadata?: Record<unknown>;
}

/** Update User System Definition */
model UpdateUserSystemDef extends SystemDef {
    system_def_type: "UpdateUserSystemDef" = "UpdateUserSystemDef";
    resource: "user";
    operation: "update";
    arguments?: UpdateUserSystemDefArguments;
}

/** Patch User System Definition Arguments */
model PatchUserSystemDefArguments {
    /** The user ID to patch */
    resource_id: uuid;
    
    /** Optional name for the user */
    name?: string;
    
    /** Optional metadata for the user */
    metadata?: Record<unknown>;
}

/** Patch User System Definition */
model PatchUserSystemDef extends SystemDef {
    system_def_type: "PatchUserSystemDef" = "PatchUserSystemDef";
    resource: "user";
    operation: "patch";
    arguments?: PatchUserSystemDefArguments;
}

/** Get User System Definition Arguments */
model GetUserSystemDefArguments {
    /** The user ID to get */
    resource_id: uuid;
}

/** Get User System Definition */
model GetUserSystemDef extends SystemDef {
    system_def_type: "GetUserSystemDef" = "GetUserSystemDef";
    resource: "user";
    operation: "get";
    arguments?: GetUserSystemDefArguments;
}

/** List Users System Definition Arguments */
model ListUsersSystemDefArguments {
    /** Filter string */
    filter?: string;
    
    /** Maximum number of results */
    limit?: int32;
    
    /** Offset for pagination */
    offset?: int32;
}

/** List Users System Definition */
model ListUsersSystemDef extends SystemDef {
    system_def_type: "ListUsersSystemDef" = "ListUsersSystemDef";
    resource: "user";
    operation: "list";
    arguments?: ListUsersSystemDefArguments;
}

/** Delete User System Definition Arguments */
model DeleteUserSystemDefArguments {
    /** The user ID to delete */
    resource_id: uuid;
}

/** Delete User System Definition */
model DeleteUserSystemDef extends SystemDef {
    system_def_type: "DeleteUserSystemDef" = "DeleteUserSystemDef";
    resource: "user";
    operation: "delete";
    arguments?: DeleteUserSystemDefArguments;
}