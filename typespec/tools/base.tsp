import "../common";

using Common;

namespace Tools;

// AIDEV-NOTE: Basic enums and aliases shared across tool definitions.

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
    | "mailgun"
    | "remote_browser"
    | "llama_parse"
    | "ffmpeg"
    | "cloudinary"
    | "arxiv"
    | "unstructured"
    | "algolia"
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

model SecretRef {
    /** The name of the secret to reference */
    name: string;
}
