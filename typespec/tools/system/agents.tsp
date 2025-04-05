import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Create Agent System Definition */
model CreateAgentSystemDef extends SystemDef {
    system_def_type: "CreateAgentSystemDef" = "CreateAgentSystemDef";
    resource: "agent";
    operation: "create";
    arguments: {
        name: string;
        description?: string;
        instructions?: string;
        tools?: unknown[];
    };
}

/** Update Agent System Definition */
model UpdateAgentSystemDef extends SystemDef {
    system_def_type: "UpdateAgentSystemDef" = "UpdateAgentSystemDef";
    resource: "agent";
    operation: "update";
    resource_id: uuid;
    arguments: {
        name?: string;
        description?: string;
        instructions?: string;
        tools?: unknown[];
    };
}

/** Patch Agent System Definition */
model PatchAgentSystemDef extends SystemDef {
    system_def_type: "PatchAgentSystemDef" = "PatchAgentSystemDef";
    resource: "agent";
    operation: "patch";
    resource_id: uuid;
    arguments: {
        name?: string;
        description?: string;
        instructions?: string;
    };
}

/** Get Agent System Definition */
model GetAgentSystemDef extends SystemDef {
    system_def_type: "GetAgentSystemDef" = "GetAgentSystemDef";
    resource: "agent";
    operation: "get";
    resource_id: uuid;
}

/** List Agents System Definition */
model ListAgentsSystemDef extends SystemDef {
    system_def_type: "ListAgentsSystemDef" = "ListAgentsSystemDef";
    resource: "agent";
    operation: "list";
    arguments?: {
        filter?: string;
        limit?: int32;
        offset?: int32;
    };
}

/** Delete Agent System Definition */
model DeleteAgentSystemDef extends SystemDef {
    system_def_type: "DeleteAgentSystemDef" = "DeleteAgentSystemDef";
    resource: "agent";
    operation: "delete";
    resource_id: uuid;
}

/** Create Agent Tool System Definition */
model CreateAgentToolSystemDef extends SystemDef {
    system_def_type: "CreateAgentToolSystemDef" = "CreateAgentToolSystemDef";
    resource: "agent";
    operation: "create";
    resource_id: uuid;
    subresource: "tool";
    arguments: {
        name: string;
        type: string;
        description?: string;
        function?: unknown;
        integration?: unknown;
        system?: unknown;
        api_call?: unknown;
    };
}

/** Update Agent Tool System Definition */
model UpdateAgentToolSystemDef extends SystemDef {
    system_def_type: "UpdateAgentToolSystemDef" = "UpdateAgentToolSystemDef";
    resource: "agent";
    operation: "update";
    resource_id: uuid;
    subresource: "tool";
    arguments: {
        name: string;
        type?: string;
        description?: string;
        function?: unknown;
        integration?: unknown;
        system?: unknown;
        api_call?: unknown;
    };
}

/** Delete Agent Tool System Definition */
model DeleteAgentToolSystemDef extends SystemDef {
    system_def_type: "DeleteAgentToolSystemDef" = "DeleteAgentToolSystemDef";
    resource: "agent";
    operation: "delete";
    resource_id: uuid;
    subresource: "tool";
    arguments: {
        name: string;
    };
}