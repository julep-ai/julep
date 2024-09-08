import "@typespec/http";

import "../common";
import "../chat";

using TypeSpec.Http;

using Common;
using Chat;

namespace Agents;

//
// AGENT MODELS
//

model BaseAgent {
    ...HasMetadata;

    /** Name of the agent */
    name: identifierSafeUnicode = identifierSafeUnicode("");

    /** About the agent */
    about: string = "";

    /** Model name to use (gpt-4-turbo, gemini-nano etc) */
    "model": string = "";

    /** Instructions for the agent */
    instructions: string | string[] = #[];

    /** Default settings for all sessions created by this agent */
    default_settings?: DefaultChatSettings;
}


model Agent is BaseAgent {
    ...HasId;
    ...HasTimestamps;
}

/** Payload for updating a agent */
@withVisibility("create", "update")
model UpdateAgentRequest {
    ...Agent;
}

/** Payload for patching a agent */
model PatchAgentRequest is UpdateAgentRequest {}

/** Payload for creating a agent (and associated documents) */
@withVisibility("create")
model CreateAgentRequest {
    ...UpdateAgentRequest;
}

/** Payload for creating or updating a agent (and associated documents) */
@withVisibility("create", "update")
model CreateOrUpdateAgentRequest {
    @path
    id: uuid;

    ...BaseAgent;
}