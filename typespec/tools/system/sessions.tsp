import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Create Session System Definition */
model CreateSessionSystemDef extends SystemDef {
    system_def_type: "CreateSessionSystemDef" = "CreateSessionSystemDef";
    resource: "session";
    operation: "create";
    arguments: {
        name?: string;
        user_id?: uuid;
        agent_id?: uuid;
        metadata?: Record<unknown>;
    };
}

/** Update Session System Definition */
model UpdateSessionSystemDef extends SystemDef {
    system_def_type: "UpdateSessionSystemDef" = "UpdateSessionSystemDef";
    resource: "session";
    operation: "update";
    resource_id: uuid;
    arguments: {
        name?: string;
        metadata?: Record<unknown>;
    };
}

/** Patch Session System Definition */
model PatchSessionSystemDef extends SystemDef {
    system_def_type: "PatchSessionSystemDef" = "PatchSessionSystemDef";
    resource: "session";
    operation: "patch";
    resource_id: uuid;
    arguments: {
        name?: string;
        metadata?: Record<unknown>;
    };
}

/** Get Session System Definition */
model GetSessionSystemDef extends SystemDef {
    system_def_type: "GetSessionSystemDef" = "GetSessionSystemDef";
    resource: "session";
    operation: "get";
    resource_id: uuid;
}

/** List Sessions System Definition */
model ListSessionsSystemDef extends SystemDef {
    system_def_type: "ListSessionsSystemDef" = "ListSessionsSystemDef";
    resource: "session";
    operation: "list";
    arguments?: {
        filter?: string;
        limit?: int32;
        offset?: int32;
    };
}

/** Delete Session System Definition */
model DeleteSessionSystemDef extends SystemDef {
    system_def_type: "DeleteSessionSystemDef" = "DeleteSessionSystemDef";
    resource: "session";
    operation: "delete";
    resource_id: uuid;
}

/** Chat Session System Definition */
model ChatSessionSystemDef extends SystemDef {
    system_def_type: "ChatSessionSystemDef" = "ChatSessionSystemDef";
    resource: "session";
    operation: "chat";
    resource_id: uuid;
    arguments: {
        /** The chat message to send */
        message: string;
        /** Optional tool choice specification */
        tool_choice?: string;
        /** Optional API key for custom model */
        x_custom_api_key?: string;
    };
}

/** Get Session History System Definition */
model GetSessionHistorySystemDef extends SystemDef {
    system_def_type: "GetSessionHistorySystemDef" = "GetSessionHistorySystemDef";
    resource: "session";
    operation: "history";
    resource_id: uuid;
    arguments?: {
        limit?: int32;
        before?: string;
    };
}