import "../agents";
import "../common";
import "../users";

using Agents;
using Common;
using Users;

namespace Sessions;

//
// SESSION MODELS
//

model Session {
    ...HasId;
    ...HasMetadata;
    ...HasTimestamps;

    /** User ID of user associated with this session */
    @visibility("create")
    user_id: User.id;

    /** Agent ID of agent associated with this session */
    @visibility("create")
    agent_id: Agent.id;

    /** A specific situation that sets the background for this session */
    situation: string = "";

    /** Summary (null at the beginning) - generated automatically after every interaction */
    @visibility("read")
    summary: string | null = null;

    /** Render system and assistant message content as jinja templates */
    render_templates: boolean = false;

    /** Threshold value for the adaptive context functionality */
    token_budget: int | null = null
    
    /** Action to start on context window overflow */
    context_overflow: string | null = null
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