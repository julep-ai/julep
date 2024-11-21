import "../common";

using Common;

namespace Tools;

//
// TOOL MODELS
//

// TODO: Split these into different files

/** A valid HTTP method */
alias httpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH" | "HEAD" | "OPTIONS" | "CONNECT" | "TRACE";

/** Integration provider name */
alias integrationProvider = (
    | "dummy"
    | "weather"
    | "wikipedia"
    | "spider"
    | "brave"
    | "browserbase"
    | "email"
    | "remote_browser"
    | "llama_parse"
    | "ffmpeg"
    | "cloudinary"
);

enum ToolType {
    /** A tool that emulates a function call */
    function,

    /** A tool that uses one of the Julep integrations */
    integration,

    /** A tool that uses a system resource */
    system,

    /** A tool that makes an API call */
    api_call,

    /** (Alpha) Anthropic new tools */
    computer_20241022,
    text_editor_20241022,
    bash_20241022,
}

/** The parameters the functions accepts, described as a JSON Schema object. */
alias FunctionParameters = Record<unknown>;

alias ToolOutput = Record<unknown>;

alias ToolChoiceOption = "auto" | "none" | NamedToolChoice;

/** Function definition */
model FunctionDef {
    /** DO NOT USE: This will be overriden by the tool name. Here only for compatibility reasons. */
    name?: null = null;

    /** DO NOT USE: This will be overriden by the tool description. Here only for compatibility reasons. */
    description?: null = null;

    /** The parameters the function accepts */
    parameters?: FunctionParameters;

}

/** Integration definition */
@discriminator("provider")
model BaseIntegrationDef {
    /** The provider of the integration */
    provider: integrationProvider;

    /** The specific method of the integration to call */
    method?: string;

    /** The setup parameters the integration accepts */
    setup?: unknown;

    /** The arguments to pre-apply to the integration call */
    arguments?: unknown;
}

model DummyIntegrationDef extends BaseIntegrationDef {
    provider: "dummy" = "dummy";
}

model BaseProviderCard {
    provider: integrationProvider;
    setup: unknown;
    methods: ProviderMethod<unknown, unknown>[];
    info: ProviderInfo;
}

model ProviderMethod<Arguments, Output> {
    method: string;
    description?: string;
    arguments?: Arguments;
    output?: Output;
}

model ProviderInfo {
    url?: url;
    docs?: url;
    icon?: url;
    friendly_name?: string;
}

alias IntegrationDef = (
    | DummyIntegrationDef
    | BraveIntegrationDef
    | EmailIntegrationDef
    | SpiderIntegrationDef
    | WikipediaIntegrationDef
    | WeatherIntegrationDef
    | BrowserbaseIntegrationDef
    | RemoteBrowserIntegrationDef
    | LlamaParseIntegrationDef
    | FfmpegIntegrationDef
    | CloudinaryIntegrationDef
);

//
// SYSTEM TOOL MODELS
//

alias resourceType = (
    | "agent"
    | "user"
    | "task"
    | "execution"
    | "doc"
    | "session"
    | "job"
);

alias subresourceType = (
    | "tool"
    | "doc"
    | "execution"
    | "transition"
);

alias operationType = (
    | "create"
    | "update"
    | "patch"
    | "create_or_update"
    | "embed"
    | "change_status"
    | "search"
    | "chat"
    | "history"
    | "delete"
    | "get"
    | "list"
);

// TODO: Add granular definitions for each system call

/** System definition */
model SystemDef {
    /** Resource is the name of the resource to use */
    resource: resourceType;

    /** Operation is the name of the operation to perform */
    operation: operationType;

    /** Resource id (if applicable) */
    resource_id?: uuid;

    /** Sub-resource type (if applicable) */
    subresource?: subresourceType;

    /** The arguments to pre-apply to the system call */
    arguments?: FunctionParameters;
}

/** API call definition */
model ApiCallDef {
    /** The HTTP method to use */
    method: httpMethod;

    /** The URL to call */
    url: url;

    /** The schema of the response */
    schema?: Record<unknown>;

    /** The headers to send with the request */
    headers?: Record<string>;

    /** The content as base64 to send with the request */
    content?: string;

    /** The data to send as form data */
    data?: Record<unknown>;

    /** The data to send as files data */
    files?: Record<unknown>;

    /** JSON body to send with the request */
    json?: Record<unknown>;

    /** Cookies */
    cookies?: Record<string>;

    /** The parameters to send with the request */
    params?: string | Record<unknown>;

    /** Follow redirects */
    follow_redirects?: boolean;

    /** The timeout for the request */
    timeout?: uint8;
}


model Tool {
    /** Name of the tool (must be unique for this agent and a valid python identifier string )*/
    name: validPythonIdentifier;

    /** Type of the tool */
    type: ToolType;

    /** Description of the tool */
    description?: string;

    /** The function to call */
    function?: FunctionDef;

    /** The integration to call */
    integration?: IntegrationDef;

    /** The system to call */
    system?: SystemDef;

    /** The API call to make */
    api_call?: ApiCallDef;

    /** (Alpha) Anthropic new tools */
    computer_20241022?: Computer20241022Def;
    text_editor_20241022?: TextEditor20241022Def;
    bash_20241022?: Bash20241022Def;

    ...HasTimestamps;
    ...HasId;
}

model FunctionCallOption {
    /** The name of the function */
    name: string;

    /** The parameters to pass to the function */
    arguments?: string; // May be a JSON string
}

model NamedToolChoice {
    function?: FunctionCallOption;
    integration?: never;
    system?: never;
    api_call?: never;
}

model ToolResponse {
    @key id: string;

    /** The output of the tool */
    output: ToolOutput;
}

/** Payload for creating a tool */
@withVisibility("create")
model CreateToolRequest {
    ...Tool;
}

/** Payload for updating a tool */
@withVisibility("update")
model UpdateToolRequest {
    ...Tool;
}

/** Payload for patching a tool */
model PatchToolRequest is UpdateToolRequest {}

/** The response tool value generated by the model */
model BaseChosenToolCall {
    /** Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now) */
    type: ToolType;

    function?: FunctionCallOption;
    integration?: unknown; // ChosenIntegrationCall
    system?: unknown; // ChosenSystemCall
    api_call?: unknown; // ChosenApiCall

    /** (Alpha) Anthropic new tools */
    computer_20241022?: ChosenComputer20241022;
    text_editor_20241022?: ChosenTextEditor20241022;
    bash_20241022?: ChosenBash20241022;

    @visibility("read")
    id?: string;
}

model ChosenFunctionCall extends BaseChosenToolCall {
    type: ToolType.function;

    /** The function to call */
    function: FunctionCallOption;
}

alias ChosenToolCall = (
    | ChosenFunctionCall
    // | ChosenIntegrationCall
    // | ChosenSystemCall
    // | ChosenApiCall
    | ChosenComputer20241022
    | ChosenTextEditor20241022
    | ChosenBash20241022
);
