import "./base.tsp";

using Tools;

namespace Tools;

// AIDEV-NOTE: Function tool specific models split from models.tsp.

/** Function definition */
model FunctionDef {
    /** DO NOT USE: This will be overriden by the tool name. Here only for compatibility reasons. */
    name?: null = null;

    /** DO NOT USE: This will be overriden by the tool description. Here only for compatibility reasons. */
    description?: null = null;

    /** The parameters the function accepts */
    parameters?: FunctionParameters;
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
