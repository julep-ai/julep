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

model Agent {
    ...HasId;
    ...HasMetadata;
    ...HasTimestamps;

    /** Name of the agent */
    name: displayName;

    /** Canonical name of the agent */
    canonical_name?: canonicalName;

    /** About the agent */
    about: string = "";

    /** Model name to use (gpt-4-turbo, gemini-nano etc) */
    "model": string = "";

    /** Instructions for the agent */
    instructions: string | string[] = #[];

    /** Default settings for all sessions created by this agent */
    default_settings?: Record<unknown>;

    /** Default system template for all sessions created by this agent */
    default_system_template: string = defaultSessionSystemMessage;
}

/** Payload for updating a agent */
@withVisibility(Lifecycle.Create, Lifecycle.Update)
model UpdateAgentRequest {
    ...Agent;
}

/** Payload for patching a agent */
model PatchAgentRequest is UpdateAgentRequest {}

/** Payload for creating a agent (and associated documents) */
@withVisibility(Lifecycle.Create)
model CreateAgentRequest {
    ...UpdateAgentRequest;
}

model CreateOrUpdateAgentRequest extends CreateAgentRequest {
    @path
    id: uuid;
    ...UpdateAgentRequest;
}