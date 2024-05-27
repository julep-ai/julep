from uuid import UUID


from ..utils import cozo_query


@cozo_query
def proc_mem_context_query(
    session_id: UUID,
    tool_query_embedding: list[float],
    doc_query_embedding: list[float],
    tools_confidence: float = 0,
    docs_confidence: float = 0.4,
    k_tools: int = 3,
    k_docs: int = 3,
) -> tuple[str, dict]:
    """Executes a complex query to retrieve memory context based on session ID, tool and document embeddings.

    Parameters:
        session_id (UUID),
        doc_query_embedding (list[float]),
        tools_confidence (float),
        docs_confidence (float),
        k_tools (int),
        k_docs (int),
        client (CozoClient).

    Return type:
        A pandas DataFrame containing the query results.
    """
    VECTOR_SIZE = 1024
    session_id = str(session_id)

    tools_radius: float = 1.0 - tools_confidence
    docs_radius: float = 1.0 - docs_confidence

    # Define the datalog query to collect memory context.
    query = f"""
    {{
        # Input table for the query
        # (This is temporary to this query)
        input[session_id, doc_query] <- [[
            to_uuid($session_id),
            # $tool_query_embedding,
            $doc_query_embedding,
        ]]

        ?[session_id, doc_query, agent_id, user_id] :=
            input[session_id, doc_query],
            *session_lookup{{
                session_id,
                agent_id,
                user_id,
            }}

        :create _input {{
            session_id: Uuid,
            agent_id: Uuid,
            user_id: Uuid?,
            # tool_query: <F32; {VECTOR_SIZE}>,
            doc_query: <F32; {VECTOR_SIZE}>,
        }}
    }} {{
        # Collect situation details based on session ID.
        # Collect situation
        ?[role, name, content, token_count, created_at, index] :=
            *_input{{session_id}},
            *sessions{{
                session_id,
                situation: content,
                created_at,
                @ "NOW"
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
            content = concat('About me (', agent_name, ') ', about),
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
            content = concat('About the user ', if(length(user_name) > 0, concat('(', user_name, ') '), ""), about),
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
            index: Float,
        }}
    }} {{
        # Collect tool information based on agent ID and tool query embedding.
        # Collect all tools

        # Search for tools
        ?[role, name, content, token_count, created_at, index] :=
            *_input{{agent_id}},
            # ~agent_functions:embedding_space {{
            #     agent_id,
            #     name: fn_name,
            #     description,
            #     parameters,
            #     updated_at: created_at |
            #     query: tool_query,
            #     k: $k_tools,
            #     ef: 128,
            #     radius: $tools_radius,
            #     bind_distance: distance,
            # }},
            *agent_functions {{
                agent_id,
                name: fn_name,
                description,
                parameters,
                updated_at: created_at,
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
            index: Float,
        }}
    }} {{
        # Collect document information based on agent ID and document query embedding.
        # Collect agent docs

        # Search for agent docs
        ?[role, name, content, token_count, created_at, index, agent_doc_id, user_doc_id] :=
            *_input{{agent_id, doc_query}},
            *agent_docs {{
                agent_id,
                doc_id: agent_doc_id,
                created_at,
            }},
            ~information_snippets:embedding_space {{
                doc_id: agent_doc_id,
                snippet_idx,
                title,
                snippet |
                query: doc_query,
                k: $k_docs,
                ef: 128,
                radius: $docs_radius,
                bind_distance: distance,
            }},
            role = "system",
            name = "information",
            content = concat(title, ':\n...', snippet),
            num_chars = length(content),
            token_count = to_int(num_chars / 3.5),
            index = 5 + (snippet_idx * 0.01),
            user_doc_id = null,

        # Save in temp table
        :create _agent_docs {{
            role: String,
            content: String,
            token_count: Int,
            created_at: Float,
            index: Float,
            name: String? default null,
            agent_doc_id: Uuid? default null,
            user_doc_id: Uuid? default null,
        }}
    }} {{
        # Collect document information based on user ID and document query embedding.
        # Collect user docs

        # Search for user docs
        ?[role, name, content, token_count, created_at, index, user_doc_id, agent_doc_id] :=
            *_input{{user_id, doc_query}},
            *user_docs {{
                user_id,
                doc_id: user_doc_id,
                created_at,
            }},
            ~information_snippets:embedding_space {{
                doc_id: user_doc_id,
                snippet_idx,
                title,
                snippet |
                query: doc_query,
                k: $k_docs,
                ef: 128,
                radius: $docs_radius,
                bind_distance: distance,
            }},
            role = "system",
            name = "information",
            content = concat(title, ':\n...', snippet),
            num_chars = length(content),
            token_count = to_int(num_chars / 3.5),
            index = 5 + (snippet_idx * 0.01),
            agent_doc_id = null,

        # Save in temp table
        :create _user_docs {{
            role: String,
            content: String,
            token_count: Int,
            created_at: Float,
            index: Float,
            name: String? default null,
            agent_doc_id: Uuid? default null,
            user_doc_id: Uuid? default null,
        }}
    }} {{
        # Collect all entries related to the session.
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
            not *relations {{
                relation: "summary_of",
                tail: entry_id,
            }},
            index = 6,
            source == "api_request" || source == "api_response" || source == "summarizer",

        # Save in temp table
        :create _entries {{
            role: String,
            name: String?,
            content: String,
            token_count: Int,
            created_at: Float,
            index: Float,
        }}
    }} {{
        # Combine all collected data into a structured format.
        # Combine all
        ?[role, name, content, token_count, created_at, index, agent_doc_id, user_doc_id] :=
            *_preamble{{
                role, name, content, token_count, created_at, index,
            }},
            agent_doc_id = null, user_doc_id = null,

        # Now let's get instructions
        ?[role, name, content, token_count, created_at, index, agent_doc_id, user_doc_id] :=
            *_input{{agent_id}},
            *agents{{
                agent_id,
                instructions,
                created_at,
            }},
            role = "system",
            name = "instruction",
            index = 3,
            content = instruction,
            token_count = round(length(instruction) / 3.5),
            instruction in instructions,
            agent_doc_id = null, user_doc_id = null,

        ?[role, name, content, token_count, created_at, index, agent_doc_id, user_doc_id] :=
            *_tools{{
                role, name, content, token_count, created_at, index
            }},
            agent_doc_id = null, user_doc_id = null,

        ?[role, name, content, token_count, created_at, index, agent_doc_id, user_doc_id] :=
            *_agent_docs {{
                role, name, content, token_count, created_at, index, agent_doc_id
            }},
            user_doc_id = null,
        
        ?[role, name, content, token_count, created_at, index, agent_doc_id, user_doc_id] :=
            *_user_docs {{
                role, name, content, token_count, created_at, index, user_doc_id
            }},
            agent_doc_id = null,

        ?[role, name, content, token_count, created_at, index, agent_doc_id, user_doc_id] :=
            *_entries{{
                role, name, content, token_count, created_at, index
            }},
            agent_doc_id = null, user_doc_id = null,

        :sort index, created_at
    }}
    """

    return (
        query,
        {
            "session_id": session_id,
            "tool_query_embedding": tool_query_embedding,
            "doc_query_embedding": doc_query_embedding,
            "k_tools": k_tools,
            "tools_radius": round(tools_radius, 2),
            "k_docs": k_docs,
            "docs_radius": round(docs_radius, 2),
        },
    )
