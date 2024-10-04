import "../common";

using Common;

namespace Tools;

//
// FUNCTION TOOL MODELS
//

/** The parameters the functions accepts, described as a JSON Schema object. */
alias FunctionParameters = Record<unknown>;

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
    name: validPythonIdentifier;
}
