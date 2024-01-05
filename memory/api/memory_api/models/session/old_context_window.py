def context_window_query_beliefs(session_id):
    return f"""
{{
    # Goal of this block is to get:
    # - character_id, user_id from session_id
    # - get session.situation
    # - also try to see if there's an entry with 'situation' type
    # - return all this
    input[
        session_id,
        dialog_embedding,
    ] <- [[
        to_uuid('{session_id}'),
        rand_vec(1024),
    ]]
    
    session[
        character_id,
        session_id,
        user_id,
        situation,
        updated_at,
        dialog_embedding,
    ] := input[
            session_id,
            dialog_embedding,
        ],
        *sessions{{
            character_id,
            user_id,
            situation,
            updated_at: validity,
            @ 'NOW'
        }}, updated_at = to_int(validity)

    ?[
        latest_entry_situation,
        latest_entry_timestamp,
        character_id,
        session_id,
        user_id,
        situation,
        dialog_embedding,
    ] := session[
            character_id,
            session_id,
            user_id,
            situation,
            updated_at,
            dialog_embedding,
        ],
        *entries {{
            name,
            role,
            content: latest_entry_situation,
            timestamp: latest_entry_timestamp,
        }}, role = 'system', name = 'situation'
    
    
    ?[
        latest_entry_situation,
        latest_entry_timestamp,
        character_id,
        session_id,
        user_id,
        situation,
        dialog_embedding,
    ] := session[
            character_id,
            session_id,
            user_id,
            situation,
            updated_at,
            dialog_embedding,
        ],
        latest_entry_situation = null,
        latest_entry_timestamp = updated_at,
    
    :sort -latest_entry_timestamp
    :limit 1

    # Tables created inside these blocks are temporary and discarded after query ends
    :create _t1 {{
        latest_entry_situation,
        latest_entry_timestamp,
        character_id,
        session_id,
        user_id,
        situation,
        dialog_embedding,
    }}
}}

{{
    # In this block, we pick between session.situation and latest situation entry if any
    ?[situation, situation_timestamp] := *_t1 {{
        latest_entry_situation: situation,
        latest_entry_timestamp: situation_timestamp,
        situation: _,
    }}, situation != null

    ?[situation, situation_timestamp] := *_t1 {{
        latest_entry_situation: _,
        latest_entry_timestamp: situation_timestamp,
        situation,
    }}

    :limit 1
    :create _t2 {{
        situation,
        situation_timestamp,
    }}
}}

{{
    # In this block, we get model settings based on character.model
    ?[
        model_name,
        max_length,
        default_settings,
    ] := *_t1{{
            character_id,
        }},
        *characters {{
            character_id,
            model: model_name,
        }},
        *models {{
            model_name,
            max_length,
            default_settings,
            @ 'NOW'
        }}
    
    :create _t3 {{
        model_name,
        max_length,
        default_settings,
    }}
}}

{{
    # In this, get user.name, user.about, character.name, character.about
    ?[
        user_name,
        user_about,
        character_name,
        character_about,
    ] := *_t1 {{
        character_id,
        user_id,
    }}, *users {{
        user_id,
        name: user_name,
        about: user_about,
    }}, *characters {{
        character_id,
        name: character_name,
        about: character_about,
    }}
        
    :create _t4 {{
        user_name,
        user_about,
        character_name,
        character_about,
    }}
}}

{{
    # Get all entries in session where parent == null (top nodes)
    # and filter out situation tags
    ?[
        entry_id,
        timestamp,
        role,
        name,
        content,
        token_count,
    ] := *_t1 {{
        session_id,
    }}, *entries {{
        entry_id,
        session_id,
        timestamp,
        role,
        name,
        content,
        token_count,
        parent_id,
    }},
    parent_id = null,
    (role != 'system' && name != 'situation')

    :sort timestamp
    :create _t5 {{
        entry_id,
        timestamp,
        role,
        name,
        content,
        token_count,
    }}
}}

{{
    # Get dialog (up to last 4 turns) for searching beliefs
    ?[
        timestamp,
        turn,
    ] :=
        *_t5 {{
            timestamp,
            role,
            name,
            content,
        }},
        role = 'user' or role = 'assistant',
        k = name ~ role,
        turn = k ++ ' said ' ++ content ++ '\n',

    :sort -timestamp
    :limit 4 * 2
    :create _last_4_turns {{
        turn,
        timestamp,
    }}
}}

{{
    collected[
        collect(turn),
    ] := *_last_4_turns {{ turn }}

    ?[
        dialog,
    ] :=
        collected[rev_turns],
        turns = reverse(rev_turns),
        dialog = from_substrings(turns),

    :create _dialog {{
        dialog,
    }}
}}

{{
    # Search relevant beliefs by fts
    ?[
        referrent_is_user,
        referrent_id,
        subject_is_user,
        subject_id,
        belief_id,
        belief,
        valence,
        score,
    ] :=
        *_t1 {{
            character_id,
            user_id,
            situation,
        }},
        *_dialog {{
            dialog,
        }},
        referrent_id = character_id
        or referrent_id = user_id
        or subject_id = character_id
        or subject_id = user_id
        or subject_id = null
        ,
        ~beliefs:summary {{
            referrent_is_user,
            referrent_id,
            subject_is_user,
            subject_id,
            belief_id,
            belief,
            valence,
            |
            # FIXME
            query: situation ++ '\n\n' ++ regex_replace_all(dialog, "[^a-zA-Z0-9\\s]+", ""),
            k: 3 * 4,  # 3 beliefs per user/character combo
            score_kind: 'tf_idf',
            bind_score: score,
        }}
    
    :create _beliefs_fts {{
        referrent_is_user,
        referrent_id,
        subject_is_user,
        subject_id,
        belief_id,
        belief,
        valence,
        score,
    }}
}}

{{
    # Search relevant beliefs by hnsw
    ?[
        referrent_is_user,
        referrent_id,
        subject_is_user,
        subject_id,
        belief_id,
        belief,
        valence,
        score,
    ] :=
        *_t1 {{
            character_id,
            user_id,
            dialog_embedding,
        }},
        referrent_id = character_id
        or referrent_id = user_id
        or subject_id = character_id
        or subject_id = user_id
        or subject_id = null
        ,
        ~beliefs:fact_embedding_space {{
            referrent_is_user,
            referrent_id,
            subject_is_user,
            subject_id,
            belief_id,
            belief,
            valence,
            |
            query: dialog_embedding,
            k: 3 * 4,  # 3 beliefs per user/character combo
            ef: 100,
            bind_distance: dist,
            radius: 100000.0,
        }},
        score = 1.0 - dist
    
    :create _beliefs_hnsw {{
        referrent_is_user,
        referrent_id,
        subject_is_user,
        subject_id,
        belief_id,
        belief,
        valence,
        score,
    }}
}}
    
{{
    beliefs[
        referrent_is_user,
        referrent_id,
        subject_is_user,
        subject_id,
        belief_id,
        belief,
        valence,
        score,
    ] :=
        *_beliefs_fts {{
            referrent_is_user,
            referrent_id,
            subject_is_user,
            subject_id,
            belief_id,
            belief,
            valence,
            score,
        }},
        *_beliefs_hnsw {{
            referrent_is_user,
            referrent_id,
            subject_is_user,
            subject_id,
            belief_id,
            belief,
            valence,
            score,
        }}

    z[
        min(score),
        max(score),
        min(valence),
        max(valence),
    ] := beliefs[
            _,
            _,
            _,
            _,
            _,
            _,
            _valence,
            score,
        ],
        valence = abs(_valence)

    adjusted[
        belief,
        belief_id,
        from_user,
        about_themselves,
        adjusted_score,
        adjusted_valence,
    ] :=
        z[
            min_score,
            max_score,
            min_valence,
            max_valence,
        ],
        beliefs[
            referrent_is_user,
            _,
            _,
            subject_id,
            belief_id,
            belief,
            valence,
            score,
        ],
        from_user = referrent_is_user,
        about_themselves = subject_id == null,
        adjusted_score = (score - min_score) / (max_score - min_score),
        adjusted_valence = (abs(valence) - min_valence) / (max_valence - min_valence),

    ?[
        statement,
        score,
        num_tokens,
    ] :=
        adjusted[
            belief,
            belief_id,
            from_user,
            about_themselves,
            adjusted_score,
            adjusted_valence,
        ],
        *_t4 {{
            character_name,
            user_name,
        }},
        prefix = cond(
            from_user && about_themselves,
            user_name ++ ' thinks about themselves that: ',
            from_user && !about_themselves,
            user_name ++ ' thinks about ' ++ character_name ++ ' that: ',
            !from_user && about_themselves,
            character_name ++ ' thinks about themselves that: ',
            !from_user && !about_themselves,
            character_name ++ ' thinks about ' ++ user_name ++ ' that: ',
        ),
        statement = concat(': ', prefix, belief, '\n'),
        score = adjusted_score * adjusted_valence,
        # FIXME
        num_tokens = length(chars(unicode_normalize(
            statement,
            'nfkd',     # https://en.wikipedia.org/wiki/Unicode_equivalence#Normal_forms
        ))),

    :sort -score
    :limit 3
    :create _t6 {{
        statement,
        score,
        num_tokens,
    }}
}}

{{
    # Collect entries together as array of jsons
    entry_list[
        collect(data),
        sum(token_count),
    ] := *_t5 {{
        entry_id,
        timestamp,
        role,
        name,
        content,
        token_count,
    }}, data = {{
        'entry_id': entry_id,
        'timestamp': timestamp,
        'role': role,
        'name': name,
        'content': content,
        'token_count': token_count,
    }}

    # Add beliefs to entries
    belief_info[
        collect(statement),
        sum(num_tokens),
    ] :=
        *_t6 {{
            statement,
            num_tokens,
        }}

    entry_list[
        collect(data),
        sum(num_tokens),
    ] :=
        belief_info[
            statements,
            num_tokens,
        ],
        formatted = concat(statements),
        data = {{
            'timestamp': 0,
            'role': 'system',
            'name': 'information',
            'content': formatted,
            'token_count': num_tokens,
        }}

    entry_list[
        collect(data),
        sum(token_count),
    ] := *_t5 {{
        entry_id,
        timestamp,
        role,
        name,
        content,
        token_count,
    }}, data = {{
        'entry_id': entry_id,
        'timestamp': timestamp,
        'role': role,
        'name': name,
        'content': content,
        'token_count': token_count,
    }}

    ?[
        model_data,
        user_data,
        character_data,
        entries,
        total_tokens,
        situation,
        situation_timestamp,
    ] := *_t2 {{
        situation,
        situation_timestamp,
    }}, *_t4 {{
        user_name,
        user_about,
        character_name,
        character_about,
    }}, *_t3 {{
        model_name,
        max_length,
        default_settings,
    }}, entry_list[entries, total_tokens_float], user_data = {{
        'name': user_name,
        'about': user_about,
    }}, character_data = {{
        'name': character_name,
        'about': character_about,
    }}, model_data = {{
        'model_name': model_name,
        'max_length': max_length,
        'default_settings': default_settings,
    }},
    total_tokens = to_int(total_tokens_float)

    :create _t7 {{
        model_data,
        user_data,
        character_data,
        entries,
        total_tokens,
        situation,
        situation_timestamp,
    }}
}}

{{
    # Add situation and about info sections on top
    ?[
        model_data,
        entries,
        total_tokens,
        character_data,
    ] := *_t7 {{
        model_data,
        user_data,
        character_data,
        entries: filtered_entries,
        total_tokens: filtered_total_tokens,
        situation,
        situation_timestamp,
    }}, 
    about_content = concat(
        'About "', get(user_data, 'name', 'User'), '": ',
        get(user_data, 'about'), '\n\n',
        'About "', get(character_data, 'name', 'Me'), '": ',
        get(character_data, 'about')
    ),
    situation_tokens = to_int(length(situation) / 3.2),
    about_tokens = to_int(length(about_content) / 3.2),
    total_tokens = filtered_total_tokens + about_tokens + situation_tokens,
    entries = concat([
        {{
            'role': 'system',
            'name': 'situation',
            'content': situation,
            'timestamp': situation_timestamp,
            'token_count': situation_tokens,
        }}, {{
            'role': 'system',
            'name': 'information',
            'content': about_content,
            'timestamp': situation_timestamp,
            'token_count': about_tokens,
        }}
    ], filtered_entries)
}}
"""
