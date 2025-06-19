import "@typespec/http";

import "../common";

using TypeSpec.Http;

using Common;

namespace Sessions;

//
// SESSION MODELS
//

model BaseDocSearch {
    /** The limit of documents to return */
    @minValue(1)
    @maxValue(50)
    limit: uint16 = 10;

    /** The language to be used for text-only search. Support for other languages coming soon. */
    lang: string = "en-US";

    /** Metadata filter to apply to the search */
    metadata_filter: MetadataFilter = #{};

    /** The number of search messages to use for the search. */
    @minValue(1)
    @maxValue(50)
    num_search_messages: uint32 = 4;

    /** The maximum query length to use for the search. */
    @minValue(100)
    @maxValue(10000)
    max_query_length: uint32 = 1000;
}

model VectorDocSearch extends BaseDocSearch {

     /** The mode to use for the search. */
    mode: "vector" = "vector";

    /** The confidence cutoff level */
    @minValue(-1)
    @maxValue(1)
    confidence: float = 0.5;

    /** MMR Strength (mmr_strength = 1 - mmr_lambda) */
    @minValue(0)
    @maxValueExclusive(1)
    mmr_strength?: float = 0.5;
}

model TextOnlyDocSearch extends BaseDocSearch {

    /** The mode to use for the search. */
    mode: "text" = "text";

    /** The trigram_similarity_threshold cutoff level */
    @minValue(0)
    @maxValue(1)
    trigram_similarity_threshold: float = 0.6;
}

model HybridDocSearch extends BaseDocSearch {

    /** The mode to use for the search. */
    mode: "hybrid" = "hybrid";

    /** The confidence cutoff level */
    @minValue(-1)
    @maxValue(1)
    confidence: float = 0.5;

    /** The weight to apply to BM25 vs Vector search results. 0 => pure BM25; 1 => pure vector; */
    @minValue(0)
    @maxValue(1)
    alpha: float = 0.5;

    /** MMR Strength (mmr_strength = 1 - mmr_lambda) */
    @minValue(0)
    @maxValueExclusive(1)
    mmr_strength?: float = 0.5;

    /** The trigram_similarity_threshold cutoff level */
    @minValue(0)
    @maxValue(1)
    trigram_similarity_threshold: float = 0.6;

    /** The k_multiplier cutoff level to control how many intermediate results to fetch before final scoring */
    @minValue(0)
    k_multiplier: int8 = 7;
}

alias DocSearch = VectorDocSearch | TextOnlyDocSearch | HybridDocSearch;

enum ContextOverflowType {
    /** Truncate the context from the top except the system prompt. */
    truncate,

    /** Automatically summarizes, clips and merges messages in the background to compress the context. */
    adaptive,
}


@discriminator("kind")
model Session {
    kind:  (
        | "single_agent_no_user"
        | "single_agent_single_user"
        | "single_agent_multi_user"
        | "multi_agent_no_user"
        | "multi_agent_single_user"
        | "multi_agent_multi_user"
    );

    /** User ID of user associated with this session */
    @visibility(Lifecycle.Create)
    user?: uuid;

    @visibility(Lifecycle.Create)
    users?: uuid[];

    /** Agent ID of agent associated with this session */
    @visibility(Lifecycle.Create)
    agent?: uuid;

    @visibility(Lifecycle.Create)
    agents?: uuid[];

    /** Session situation */
    situation: string | null = null;

    /** A specific system prompt template that sets the background for this session */
    system_template?: string;

    /** Summary (null at the beginning) - generated automatically after every interaction */
    @visibility(Lifecycle.Read)
    summary: string | null = null;

    /** Render system and assistant message content as jinja templates */
    render_templates: boolean = true;

    /** Threshold value for the adaptive context functionality */
    token_budget: uint16 | null = null;

    /** Action to start on context window overflow */
    context_overflow: ContextOverflowType | null = null;

    /** Whether to auto-run the tool and send the tool results to the model when available.
     * (default: false for sessions, true for tasks)
     * 
     * If a tool call is made, the tool's output will be sent back to the model as the model's input.
     * If a tool call is not made, the model's output will be returned as is. */
    auto_run_tools: boolean = false;

    /** Whether to forward tool calls to the model */
    forward_tool_calls: boolean = false;
    /** Recall options for the session */
    recall_options?: DocSearch | null = null;
    
    ...HasId;
    ...HasMetadata;
    ...HasTimestamps;
}

model SingleAgentNoUserSession extends Session {
    kind: "single_agent_no_user" = "single_agent_no_user";

    user?: never;
    users?: never;
    agents?: never;

    agent: uuid;
}

model SingleAgentSingleUserSession extends Session {
    kind: "single_agent_single_user" = "single_agent_single_user";

    users?: never;
    agents?: never;

    agent: uuid;
    user: uuid;
}

model SingleAgentMultiUserSession extends Session {
    kind: "single_agent_multi_user" = "single_agent_multi_user";

    user?: never;
    agents?: never;

    agent: uuid;

    @minItems(2)
    users: uuid[];
}

model MultiAgentNoUserSession extends Session {
    kind: "multi_agent_no_user" = "multi_agent_no_user";

    user?: never;
    users?: never;
    agent?: never;

    @minItems(2)
    agents: uuid[];
}

model MultiAgentSingleUserSession extends Session {
    kind: "multi_agent_single_user" = "multi_agent_single_user";

    users?: never;
    agent?: never;

    @minItems(2)
    agents: uuid[];
    user: uuid;
}

model MultiAgentMultiUserSession extends Session {
    kind: "multi_agent_multi_user" = "multi_agent_multi_user";

    user?: never;
    agent?: never;

    @minItems(2)
    agents: uuid[];

    @minItems(2)
    users: uuid[];
}


/** Payload for updating a session */
@withVisibility(Lifecycle.Update)
model UpdateSessionRequest {
    ...Session;
}

/** Payload for patching a session */
model PatchSessionRequest is UpdateSessionRequest {}

/** Payload for creating a session */
@withVisibility(Lifecycle.Create)
model CreateSessionRequest {
    ...Session;
}

@withVisibility(Lifecycle.Create, Lifecycle.Update)
model CreateOrUpdateSessionRequest extends CreateSessionRequest {
    @path
    id: uuid;

    ...CreateSessionRequest;
}
