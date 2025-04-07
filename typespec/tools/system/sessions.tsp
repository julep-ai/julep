import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Create Session System Definition Arguments */
model CreateSessionSystemDefArguments {
    /** Optional name for the session */
    name?: string;
    
    /** Optional user ID for the session */
    user_id?: uuid;
    
    /** Optional agent ID for the session */
    agent_id?: uuid;
    
    /** Optional metadata for the session */
    metadata?: Record<unknown>;
}

/** Create Session System Definition */
model CreateSessionSystemDef extends SystemDef {
    system_def_type: "CreateSessionSystemDef" = "CreateSessionSystemDef";
    resource: "session";
    operation: "create";
    arguments?: CreateSessionSystemDefArguments;
}

/** Update Session System Definition Arguments */
model UpdateSessionSystemDefArguments {
    /** The session ID to update */
    resource_id: uuid;
    
    /** Optional name for the session */
    name?: string;
    
    /** Optional metadata for the session */
    metadata?: Record<unknown>;
}

/** Update Session System Definition */
model UpdateSessionSystemDef extends SystemDef {
    system_def_type: "UpdateSessionSystemDef" = "UpdateSessionSystemDef";
    resource: "session";
    operation: "update";
    arguments?: UpdateSessionSystemDefArguments;
}

/** Patch Session System Definition Arguments */
model PatchSessionSystemDefArguments {
    /** The session ID to patch */
    resource_id: uuid;
    
    /** Optional name for the session */
    name?: string;
    
    /** Optional metadata for the session */
    metadata?: Record<unknown>;
}

/** Patch Session System Definition */
model PatchSessionSystemDef extends SystemDef {
    system_def_type: "PatchSessionSystemDef" = "PatchSessionSystemDef";
    resource: "session";
    operation: "patch";
    arguments?: PatchSessionSystemDefArguments;
}

/** Get Session System Definition Arguments */
model GetSessionSystemDefArguments {
    /** The session ID to get */
    resource_id: uuid;
}

/** Get Session System Definition */
model GetSessionSystemDef extends SystemDef {
    system_def_type: "GetSessionSystemDef" = "GetSessionSystemDef";
    resource: "session";
    operation: "get";
    arguments?: GetSessionSystemDefArguments;
}

/** List Sessions System Definition Arguments */
model ListSessionsSystemDefArguments {
    /** Filter string */
    filter?: string;
    
    /** Maximum number of results */
    limit?: int32;
    
    /** Offset for pagination */
    offset?: int32;
}

/** List Sessions System Definition */
model ListSessionsSystemDef extends SystemDef {
    system_def_type: "ListSessionsSystemDef" = "ListSessionsSystemDef";
    resource: "session";
    operation: "list";
    arguments?: ListSessionsSystemDefArguments;
}

/** Delete Session System Definition Arguments */
model DeleteSessionSystemDefArguments {
    /** The session ID to delete */
    resource_id: uuid;
}

/** Delete Session System Definition */
model DeleteSessionSystemDef extends SystemDef {
    system_def_type: "DeleteSessionSystemDef" = "DeleteSessionSystemDef";
    resource: "session";
    operation: "delete";
    arguments?: DeleteSessionSystemDefArguments;
}

/** Chat Session System Definition Arguments */
model ChatSessionSystemDefArguments {
    /** The session ID to chat with */
    resource_id: uuid;
    
    /** The chat message to send */
    message: string;
    
    /** Optional tool choice specification */
    tool_choice?: string;
    
    /** Optional API key for custom model */
    x_custom_api_key?: string;
}

/** Chat Session System Definition */
model ChatSessionSystemDef extends SystemDef {
    system_def_type: "ChatSessionSystemDef" = "ChatSessionSystemDef";
    resource: "session";
    operation: "chat";
    arguments?: ChatSessionSystemDefArguments;
}

/** Get Session History System Definition Arguments */
model GetSessionHistorySystemDefArguments {
    /** The session ID to get history for */
    resource_id: uuid;
    
    /** Maximum number of results */
    limit?: int32;
    
    /** Get entries before this cursor */
    before?: string;
}

/** Get Session History System Definition */
model GetSessionHistorySystemDef extends SystemDef {
    system_def_type: "GetSessionHistorySystemDef" = "GetSessionHistorySystemDef";
    resource: "session";
    operation: "history";
    arguments?: GetSessionHistorySystemDefArguments;
}