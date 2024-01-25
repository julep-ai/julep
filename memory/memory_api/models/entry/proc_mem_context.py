import json
from uuid import UUID


def proc_mem_context_query(
    session_id: UUID,
    tool_query_embedding: list[float],
    instruction_query_embedding: list[float],
    doc_query_embedding: list[float],
    tools_confidence: float = 0.7,
    instructions_confidence: float = 0.7,
    docs_confidence: float = 0.7,
    k_tools: int = 3,
    k_instructions: int = 10,
    k_docs: int = 2,
):
    VECTOR_SIZE = 768
    session_id = str(session_id)
    assert (
        len(tool_query_embedding)
        == len(instruction_query_embedding)
        == len(doc_query_embedding)
        == VECTOR_SIZE
    )

    tools_radius: float = 1.0 - tools_confidence
    instructions_radius: float = 1.0 - instructions_confidence
    docs_radius: float = 1.0 - docs_confidence

    return f"""
    {{
        # Input table for the query
        # (This is temporary to this query)
        input[session_id, tool_query, instruction_query, doc_query] <- [[
            to_uuid("{session_id}"),
            vec({json.dumps(tool_query_embedding)}),
            vec({json.dumps(instruction_query_embedding)}),
            vec({json.dumps(doc_query_embedding)}),
        ]]

        ?[session_id, tool_query, instruction_query, doc_query, agent_id, user_id] :=
            input[session_id, tool_query, instruction_query, doc_query],
            *session_lookup{{
                session_id,
                agent_id,
                user_id,
            }}

        :create _input {{
            session_id: Uuid,
            agent_id: Uuid,
            user_id: Uuid,
            tool_query: <F32; {VECTOR_SIZE}>,
            instruction_query: <F32; {VECTOR_SIZE}>,
            doc_query: <F32; {VECTOR_SIZE}>,
        }}
    }} {{
        # Collect situation
        ?[role, name, content, token_count, created_at, index] :=
            *_input{{session_id}},
            *sessions{{
                session_id,
                situation: content,
                created_at,
            }},
            index = 0,  # Situation entry should be the first entry
            role = "system",
            name = "situation",
            num_chars = length(content),
            token_count = to_int(num_chars / 3.5),
            num_chars > 0

        # and agent description
        ?[role, name, content, token_count, created_at, index] :=
            *_input{{agent_id}},
            *agents{{
                agent_id,
                name: agent_name,
                about,
                updated_at: created_at,
            }},
            index = 1,
            role = "system",
            name = "information",
            content = concat('About me (', agent_name, '), the agent: ', about),
            num_chars = length(content),
            token_count = to_int(num_chars / 3.5),
            num_chars > 0

        # and user description
        ?[role, name, content, token_count, created_at, index] :=
            *_input{{user_id}},
            *users{{
                user_id,
                name: user_name,
                about,
                updated_at: created_at,
            }},
            !is_null(user_id),
            index = 2,
            role = "system",
            name = "information",
            content = concat('About the user (', user_name, ')', about),
            num_chars = length(content),
            token_count = to_int(num_chars / 3.5),
            num_chars > 0

        # Save in temp table
        :create _preamble {{
            role: String,
            name: String?,
            content: String,
            token_count: Int,
            created_at: Float,
            index: Int,
        }}
    }} {{
        # Collect all instructions

        # Keep all important ones
        ?[role, name, content, token_count, created_at, index] :=
            *_input{{agent_id}},
            *agent_instructions {{
                agent_id,
                instruction_idx,
                content,
                important,
                created_at,
            }},
            important = true,
            role = "system",
            name = "instruction",
            num_chars = length(content),
            token_count = to_int(num_chars / 3.5),
            index = 3 + (instruction_idx * 0.01)

        # Search for rest of instructions
        ?[role, name, content, token_count, created_at, index] :=
            *_input{{agent_id, instruction_query}},
            ~agent_instructions:embedding_space {{
                agent_id,
                instruction_idx,
                content,
                created_at,
                important |
                query: instruction_query,
                k: {k_instructions},
                ef: 128,
                radius: {instructions_radius:.2f},
                bind_distance: distance,
                filter: important == false,
            }},
            role = "system",
            name = "instruction",
            num_chars = length(content),
            token_count = to_int(num_chars / 3.5),
            index = 3 + (instruction_idx * 0.01)

        # Save in temp table
        :create _instructions {{
            role: String,
            name: String?,
            content: String,
            token_count: Int,
            created_at: Float,
            index: Int,
        }}
    }} {{
        # Collect all tools

        # Search for tools
        ?[role, name, content, token_count, created_at, index] :=
            *_input{{agent_id, tool_query}},
            ~agent_functions:embedding_space {{
                agent_id,
                name: fn_name,
                description,
                parameters,
                updated_at: created_at |
                query: tool_query,
                k: {k_tools},
                ef: 128,
                radius: {tools_radius:.2f},
                bind_distance: distance,
            }},

            role = "system",
            name = "functions",
            fn_data = {{
                "name": fn_name,
                "description": description,
                "parameters": parameters
            }},
            content = dump_json(fn_data),
            num_chars = length(content),
            token_count = to_int(num_chars / 3.5),
            index = 4

        # Save in temp table
        :create _tools {{
            role: String,
            name: String?,
            content: String,
            token_count: Int,
            created_at: Float,
            index: Int,
        }}
    }} {{
        # Collect additional_info docs

        # Search for agent docs
        ?[role, name, content, token_count, created_at, index] :=
            *_input{{agent_id, doc_query}},
            *agent_additional_info {{
                agent_id,
                additional_info_id,
                created_at,
            }},
            ~information_snippets:embedding_space {{
                additional_info_id,
                snippet_idx,
                title,
                snippet |
                query: doc_query,
                k: {k_docs},
                ef: 128,
                radius: {docs_radius:.2f},
                bind_distance: distance,
            }},
            role = "system",
            name = "information",
            content = concat(title, ':\n...', snippet),
            num_chars = length(content),
            token_count = to_int(num_chars / 3.5),
            index = 5 + (snippet_idx * 0.01)

        # Search for user docs
        ?[role, name, content, token_count, created_at, index] :=
            *_input{{user_id, doc_query}},
            *user_additional_info {{
                user_id,
                additional_info_id,
                created_at,
            }},
            ~information_snippets:embedding_space {{
                additional_info_id,
                snippet_idx,
                title,
                snippet |
                query: doc_query,
                k: {k_docs},
                ef: 128,
                radius: {docs_radius:.2f},
                bind_distance: distance,
            }},
            role = "system",
            name = "information",
            content = concat(title, ':\n...', snippet),
            num_chars = length(content),
            token_count = to_int(num_chars / 3.5),
            index = 5 + (snippet_idx * 0.01)

        # Save in temp table
        :create _additional_info {{
            role: String,
            name: String?,
            content: String,
            token_count: Int,
            created_at: Float,
            index: Int,
        }}
    }} {{
        # Collect all entries
        ?[role, name, content, token_count, created_at, index] :=
            *_input{{session_id}},
            *entries{{
                entry_id,
                session_id,
                source,
                role,
                name,
                content,
                token_count,
                created_at,
            }},
            not *entry_relations {{
                tail: entry_id,
            }},
            index = 6,
            source == "api_request" || source == "api_response",

        # Save in temp table
        :create _entries {{
            role: String,
            name: String?,
            content: String,
            token_count: Int,
            created_at: Float,
            index: Int,
        }}
    }} {{
        # Combine all
        ?[role, name, content, token_count, created_at, index] :=
            *_preamble{{
                role, name, content, token_count, created_at, index
            }},

        ?[role, name, content, token_count, created_at, index] :=
            *_instructions{{
                role, name, content, token_count, created_at, index
            }},

        ?[role, name, content, token_count, created_at, index] :=
            *_tools{{
                role, name, content, token_count, created_at, index
            }},

        ?[role, name, content, token_count, created_at, index] :=
            *_additional_info{{
                role, name, content, token_count, created_at, index
            }},

        ?[role, name, content, token_count, created_at, index] :=
            *_entries{{
                role, name, content, token_count, created_at, index
            }},

        :sort index, created_at
    }}
    """
