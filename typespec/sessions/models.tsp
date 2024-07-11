import "../common";

using Common;

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
    user_id: uuid;

    /** Agent ID of agent associated with this session */
    @visibility("create")
    agent_id: uuid;

    /** A specific situation that sets the background for this session */
    situation: string = "";

    /** Summary (null at the beginning) - generated automatically after every interaction */
    @visibility("read")
    summary: string | null = null;

    /** Render system and assistant message content as jinja templates */
    render_templates: boolean = false;
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