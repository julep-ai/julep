import "../common";

using Common;

namespace Tools;

/** Transport type for MCP servers */
alias McpTransport = ("sse" | "http");

/** Setup parameters for MCP integration */
model McpSetup {
    /** Transport used to connect to the MCP server */
    transport: McpTransport;

    /** (stdio) Executable or command to launch the server */
    command?: string;

    /** (stdio) Arguments for the server command */
    args?: string[] = #[];

    /** (stdio) Working directory for the server process */
    cwd?: string;

    /** (stdio) Environment variables for the server process */
    env?: Record<string> = #{};

    /** (http) Base URL for the MCP server (usually ends with /mcp) */
    http_url?: url;

    /** (http) Optional HTTP headers to include (e.g., Authorization) */
    http_headers?: Record<string> = #{};
}

/** Arguments to call a named tool on the MCP server */
model McpCallToolArguments {
    /** The MCP tool name to invoke */
    tool_name: string;

    /** JSON-serializable arguments to pass to the MCP tool */
    arguments?: Record<unknown> = #{};

    /** Optional per-call timeout in seconds */
    timeout_seconds?: uint16 = 60;
}

/** Arguments to list available tools */
model McpListToolsArguments {dummy: string = "dummy";}

/** A single MCP tool description */
model McpToolInfo {
    name: string;
    description?: string;
    /** JSON Schema for the tool input parameters, if provided by the server */
    input_schema?: Record<unknown>;
}

/** Output for listing tools from an MCP server */
model McpListToolsOutput {
    tools: McpToolInfo[];
}

/** Output for an MCP tool call */
model McpToolCallOutput {
    /** Concatenated textual content, if any was returned */
    text?: string | null = null;

    /** Structured content returned by the server, if present */
    structured?: Record<unknown> | null = null;

    /** Raw content items as returned by MCP (best-effort JSON form) */
    content?: Record<unknown>[] = #[];

    /** Whether the server indicated an error for this call */
    is_error?: boolean = false;
}

/** MCP integration definition */
model McpIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "mcp" */
    provider: "mcp" = "mcp";

    /** The specific method of the integration to call */
    method?: string;

    /** The setup parameters for MCP */
    setup?: McpSetup;

    /** The arguments for MCP methods */
    arguments?: McpCallToolArguments | McpListToolsArguments;
}

/** MCP Provider Card */
model McpProviderCard extends BaseProviderCard {
    provider: "mcp" = "mcp";
    setup: McpSetup;
    methods: ProviderMethod<McpCallToolArguments | McpListToolsArguments, McpToolCallOutput | McpListToolsOutput>[] = #[
        #{
            method: "list_tools",
            description: "List tools exposed by an MCP server",
        },
        #{
            method: "call_tool",
            description: "Call a named tool on an MCP server",
        }
    ];
    info: ProviderInfo = #{
        url: "https://modelcontextprotocol.io/",
        docs: "https://spec.modelcontextprotocol.io/",
        icon: "https://modelcontextprotocol.io/favicon.ico",
        friendly_name: "Model Context Protocol",
    };
}

