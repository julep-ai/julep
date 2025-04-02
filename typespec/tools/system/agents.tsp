import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Create Agent System Definition */
model CreateAgentSystemDef extends SystemDef {
    systemDefType: "CreateAgentSystemDef";
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
    systemDefType: "UpdateAgentSystemDef";
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
    systemDefType: "PatchAgentSystemDef";
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
    systemDefType: "GetAgentSystemDef";
    resource: "agent";
    operation: "get";
    resource_id: uuid;
}

/** List Agents System Definition */
model ListAgentsSystemDef extends SystemDef {
    systemDefType: "ListAgentsSystemDef";
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
    systemDefType: "DeleteAgentSystemDef";
    resource: "agent";
    operation: "delete";
    resource_id: uuid;
}

/** Create Agent Tool System Definition */
model CreateAgentToolSystemDef extends SystemDef {
    systemDefType: "CreateAgentToolSystemDef";
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
    systemDefType: "UpdateAgentToolSystemDef";
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
    systemDefType: "DeleteAgentToolSystemDef";
    resource: "agent";
    operation: "delete";
    resource_id: uuid;
    subresource: "tool";
    arguments: {
        name: string;
    };
}