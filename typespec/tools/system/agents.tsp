import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Create Agent System Definition Arguments */
model CreateAgentSystemDefArguments {
    /** Name of the agent */
    name: string;
    
    /** Optional description for the agent */
    description?: string;
    
    /** Optional instructions for the agent */
    instructions?: string;
    
    /** Optional tools for the agent */
    tools?: unknown[];
}

/** Create Agent System Definition */
model CreateAgentSystemDef extends SystemDef {
    system_def_type: "CreateAgentSystemDef" = "CreateAgentSystemDef";
    resource: "agent";
    operation: "create";
    arguments?: CreateAgentSystemDefArguments;
}

/** Update Agent System Definition Arguments */
model UpdateAgentSystemDefArguments {
    /** The agent ID to update */
    resource_id: uuid;
    
    /** Optional name for the agent */
    name?: string;
    
    /** Optional description for the agent */
    description?: string;
    
    /** Optional instructions for the agent */
    instructions?: string;
    
    /** Optional tools for the agent */
    tools?: unknown[];
}

/** Update Agent System Definition */
model UpdateAgentSystemDef extends SystemDef {
    system_def_type: "UpdateAgentSystemDef" = "UpdateAgentSystemDef";
    resource: "agent";
    operation: "update";
    arguments?: UpdateAgentSystemDefArguments;
}

/** Patch Agent System Definition Arguments */
model PatchAgentSystemDefArguments {
    /** The agent ID to patch */
    resource_id: uuid;
    
    /** Optional name for the agent */
    name?: string;
    
    /** Optional description for the agent */
    description?: string;
    
    /** Optional instructions for the agent */
    instructions?: string;
}

/** Patch Agent System Definition */
model PatchAgentSystemDef extends SystemDef {
    system_def_type: "PatchAgentSystemDef" = "PatchAgentSystemDef";
    resource: "agent";
    operation: "patch";
    arguments?: PatchAgentSystemDefArguments;
}

/** Get Agent System Definition Arguments */
model GetAgentSystemDefArguments {
    /** The agent ID to get */
    resource_id: uuid;
}

/** Get Agent System Definition */
model GetAgentSystemDef extends SystemDef {
    system_def_type: "GetAgentSystemDef" = "GetAgentSystemDef";
    resource: "agent";
    operation: "get";
    arguments?: GetAgentSystemDefArguments;
}

/** List Agents System Definition Arguments */
model ListAgentsSystemDefArguments {
    /** Filter string */
    filter?: string;
    
    /** Maximum number of results */
    limit?: int32;
    
    /** Offset for pagination */
    offset?: int32;
}

/** List Agents System Definition */
model ListAgentsSystemDef extends SystemDef {
    system_def_type: "ListAgentsSystemDef" = "ListAgentsSystemDef";
    resource: "agent";
    operation: "list";
    arguments?: ListAgentsSystemDefArguments;
}

/** Delete Agent System Definition Arguments */
model DeleteAgentSystemDefArguments {
    /** The agent ID to delete */
    resource_id: uuid;
}

/** Delete Agent System Definition */
model DeleteAgentSystemDef extends SystemDef {
    system_def_type: "DeleteAgentSystemDef" = "DeleteAgentSystemDef";
    resource: "agent";
    operation: "delete";
    arguments?: DeleteAgentSystemDefArguments;
}

/** Create Agent Tool System Definition Arguments */
model CreateAgentToolSystemDefArguments {
    /** The agent ID to add the tool to */
    resource_id: uuid;
    
    /** Name of the tool */
    name: string;
    
    /** Type of the tool */
    type: string;
    
    /** Optional description for the tool */
    description?: string;
    
    /** Optional function specification */
    function?: unknown;
    
    /** Optional integration specification */
    integration?: unknown;
    
    /** Optional system specification */
    system?: unknown;
    
    /** Optional API call specification */
    api_call?: unknown;
}

/** Create Agent Tool System Definition */
model CreateAgentToolSystemDef extends SystemDef {
    system_def_type: "CreateAgentToolSystemDef" = "CreateAgentToolSystemDef";
    resource: "agent";
    operation: "create";
    subresource: "tool";
    arguments?: CreateAgentToolSystemDefArguments;
}

/** Update Agent Tool System Definition Arguments */
model UpdateAgentToolSystemDefArguments {
    /** The agent ID that owns the tool */
    resource_id: uuid;
    
    /** Name of the tool to update */
    name: string;
    
    /** Optional type of the tool */
    type?: string;
    
    /** Optional description for the tool */
    description?: string;
    
    /** Optional function specification */
    function?: unknown;
    
    /** Optional integration specification */
    integration?: unknown;
    
    /** Optional system specification */
    system?: unknown;
    
    /** Optional API call specification */
    api_call?: unknown;
}

/** Update Agent Tool System Definition */
model UpdateAgentToolSystemDef extends SystemDef {
    system_def_type: "UpdateAgentToolSystemDef" = "UpdateAgentToolSystemDef";
    resource: "agent";
    operation: "update";
    subresource: "tool";
    arguments?: UpdateAgentToolSystemDefArguments;
}

/** Delete Agent Tool System Definition Arguments */
model DeleteAgentToolSystemDefArguments {
    /** The agent ID that owns the tool */
    resource_id: uuid;
    
    /** Name of the tool to delete */
    name: string;
}

/** Delete Agent Tool System Definition */
model DeleteAgentToolSystemDef extends SystemDef {
    system_def_type: "DeleteAgentToolSystemDef" = "DeleteAgentToolSystemDef";
    resource: "agent";
    operation: "delete";
    subresource: "tool";
    arguments?: DeleteAgentToolSystemDefArguments;
}