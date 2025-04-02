import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Create Session System Definition */
model CreateSessionSystemDef extends SystemDef {
    systemDefType: "CreateSessionSystemDef";
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
    systemDefType: "UpdateSessionSystemDef";
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
    systemDefType: "PatchSessionSystemDef";
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
    systemDefType: "GetSessionSystemDef";
    resource: "session";
    operation: "get";
    resource_id: uuid;
}

/** List Sessions System Definition */
model ListSessionsSystemDef extends SystemDef {
    systemDefType: "ListSessionsSystemDef";
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
    systemDefType: "DeleteSessionSystemDef";
    resource: "session";
    operation: "delete";
    resource_id: uuid;
}

/** Chat Session System Definition */
model ChatSessionSystemDef extends SystemDef {
    systemDefType: "ChatSessionSystemDef";
    resource: "session";
    operation: "chat";
    resource_id: uuid;
    arguments: {
        message: string;
        tool_choice?: string;
    };
}

/** Get Session History System Definition */
model GetSessionHistorySystemDef extends SystemDef {
    systemDefType: "GetSessionHistorySystemDef";
    resource: "session";
    operation: "history";
    resource_id: uuid;
    arguments?: {
        limit?: int32;
        before?: string;
    };
}