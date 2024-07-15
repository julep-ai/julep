import "../common";

using Common;

namespace Sessions;

//
// SESSION MODELS
//

@discriminator("__kind")
model Session {
    @visibility("none")
    __kind:  (
        | "single_agent_no_user"
        | "single_agent_single_user"
        | "single_agent_multi_user"
        | "multi_agent_no_user"
        | "multi_agent_single_user"
        | "multi_agent_multi_user"
    );

    /** User ID of user associated with this session */
    @visibility("create")
    user?: uuid;

    @visibility("create")
    users?: uuid[];

    /** Agent ID of agent associated with this session */
    @visibility("create")
    agent?: uuid;

    @visibility("create")
    agents?: uuid[];

    /** A specific situation that sets the background for this session */
    situation: string = defaultSessionSystemMessage;

    /** Summary (null at the beginning) - generated automatically after every interaction */
    @visibility("read")
    summary: string | null = null;

    /** Render system and assistant message content as jinja templates */
    render_templates: boolean = false;

    /** Threshold value for the adaptive context functionality */
    token_budget: uint16 | null = null;
    
    /** Action to start on context window overflow */
    context_overflow: string | null = null;

    ...HasId;
    ...HasMetadata;
    ...HasTimestamps;
}

model SingleAgentNoUserSession extends Session {
    @visibility("none")
    __kind: "single_agent_no_user" = "single_agent_no_user";

    user?: never;
    users?: never;
    agents?: never;

    agent: uuid;
}

model SingleAgentSingleUserSession extends Session {
    @visibility("none")
    __kind: "single_agent_single_user" = "single_agent_single_user";

    users?: never;
    agents?: never;

    agent: uuid;
    user: uuid;
}

model SingleAgentMultiUserSession extends Session {
    @visibility("none")
    __kind: "single_agent_multi_user" = "single_agent_multi_user";

    user?: never;
    agents?: never;

    agent: uuid;
    users: uuid[];
}

model MultiAgentNoUserSession extends Session {
    @visibility("none")
    __kind: "multi_agent_no_user" = "multi_agent_no_user";

    user?: never;
    users?: never;
    agent?: never;

    agents: uuid[];
}

model MultiAgentSingleUserSession extends Session {
    @visibility("none")
    __kind: "multi_agent_single_user" = "multi_agent_single_user";

    users?: never;
    agent?: never;

    agents: uuid[];
    user: uuid;
}

model MultiAgentMultiUserSession extends Session {
    @visibility("none")
    __kind: "multi_agent_multi_user" = "multi_agent_multi_user";

    user?: never;
    agent?: never;

    agents: uuid[];
    users: uuid[];
}


/** Payload for updating a session */
@withVisibility("update")
model UpdateSessionRequest {
    ...Session;
}

/** Payload for patching a session */
model PatchSessionRequest is UpdateSessionRequest {}

/** Payload for creating a session */
@withVisibility("create")
model CreateSessionRequest {
    ...Session;
}

@withVisibility("create", "update")
model CreateOrUpdateSessionRequest {
    id: uuid;

    ...CreateSessionRequest;
}