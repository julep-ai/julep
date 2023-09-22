context_window_query = """
{
    # Goal of this block is to get:
    # - character_id, user_id from session_id
    # - get session.situation
    # - also try to see if there's an entry with "situation" type
    # - return all this
    input[session_id] <- [[
        to_uuid("{session_id}"),
    ]]
    
    session[
        character_id,
        session_id,
        user_id,
        situation,
        updated_at,
    ] := input[session_id],
        *sessions{
            character_id,
            user_id,
            situation,
            updated_at: validity,
            @ "NOW"
        }, updated_at = to_int(validity)

    ?[
        latest_entry_situation,
        latest_entry_timestamp,
        character_id,
        session_id,
        user_id,
        situation,
    ] := session[
            character_id,
            session_id,
            user_id,
            situation,
            updated_at,
        ],
        *entries {
            name,
            role,
            content: latest_entry_situation,
            timestamp: latest_entry_timestamp,
        }, role = "system", name = "situation"
    
    
    ?[
        latest_entry_situation,
        latest_entry_timestamp,
        character_id,
        session_id,
        user_id,
        situation,
    ] := session[
            character_id,
            session_id,
            user_id,
            situation,
            updated_at,
        ],
        latest_entry_situation = null,
        latest_entry_timestamp = updated_at,
    
    :sort -latest_entry_timestamp
    :limit 1

    # Tables created inside these blocks are temporary and discarded after query ends
    :create _t1 {
        latest_entry_situation,
        latest_entry_timestamp,
        character_id,
        session_id,
        user_id,
        situation,
    }
}

{
    # In this block, we pick between session.situation and latest situation entry if any
    ?[situation, situation_timestamp] := *_t1 {
        latest_entry_situation: situation,
        latest_entry_timestamp: situation_timestamp,
        situation: _,
    }, situation != null

    ?[situation, situation_timestamp] := *_t1 {
        latest_entry_situation: _,
        latest_entry_timestamp: situation_timestamp,
        situation,
    }

    :limit 1
    :create _t2 {
        situation,
        situation_timestamp,
    }
}

{
    # In this block, we get model settings based on character.model
    ?[
        model_name,
        max_length,
        default_settings,
    ] := *_t1{
            character_id,
        },
        *characters {
            character_id,
            model: model_name,
        },
        *models {
            model_name,
            max_length,
            default_settings,
            @ "NOW"
        }
    
    :create _t3 {
        model_name,
        max_length,
        default_settings,
    }
}

{
    # In this, get user.name, user.about, character.name, character.about
    ?[
        user_name,
        user_about,
        character_name,
        character_about,
    ] := *_t1 {
        character_id,
        user_id,
    }, *users {
        user_id,
        name: user_name,
        about: user_about,
    }, *characters {
        character_id,
        name: character_name,
        about: character_about,
    }
        
    :create _t4 {
        user_name,
        user_about,
        character_name,
        character_about,
    }
}

{
    # Get all entries in session where parent == null (top nodes)
    # and filter out situation tags
    ?[
        timestamp,
        role,
        name,
        content,
        token_count,
    ] := *_t1 {
        session_id,
    }, *entries {
        session_id,
        timestamp,
        role,
        name,
        content,
        token_count,
        parent_id,
    },
    parent_id = null,
    (role != "system" && name != "situation")

    :sort timestamp
    :create _t5 {
        timestamp,
        role,
        name,
        content,
        token_count,
    }
}

{
    # Collect entries together as array of jsons
    entry_list[
        collect(data),
        sum(token_count),
    ] := *_t5 {
        timestamp,
        role,
        name,
        content,
        token_count,
    }, data = {
        "timestamp": timestamp,
        "role": role,
        "name": name,
        "content": content,
        "token_count": token_count,
    }
    
    ?[
        model_data,
        user_data,
        character_data,
        entries,
        total_tokens,
        situation,
        situation_timestamp,
    ] := *_t2 {
        situation,
        situation_timestamp,
    }, *_t4 {
        user_name,
        user_about,
        character_name,
        character_about,
    }, *_t3 {
        model_name,
        max_length,
        default_settings,
    }, entry_list[entries, total_tokens_float], user_data = {
        "name": user_name,
        "about": user_about,
    }, character_data = {
        "name": character_name,
        "about": character_about,
    }, model_data = {
        "model_name": model_name,
        "max_length": max_length,
        "default_settings": default_settings,
    },
    total_tokens = to_int(total_tokens_float)

    :create _t6 {
        model_data,
        user_data,
        character_data,
        entries,
        total_tokens,
        situation,
        situation_timestamp,
    }
}

{
    # Add situation and about info sections on top
    ?[
        model_data,
        entries,
        total_tokens,
        character_data,
    ] := *_t6 {
        model_data,
        user_data,
        character_data,
        entries: filtered_entries,
        total_tokens: filtered_total_tokens,
        situation,
        situation_timestamp,
    }, 
    about_content = concat(
        "About '", get(user_data, "name", "User"), "': ",
        get(user_data, "about"), "\n\n",
        "About '", get(character_data, "name", "Me"), "': ",
        get(character_data, "about")
    ),
    situation_tokens = to_int(length(situation) / 3.2),
    about_tokens = to_int(length(about_content) / 3.2),
    total_tokens = filtered_total_tokens + about_tokens + situation_tokens,
    entries = concat([
        {
            "role": "system",
            "name": "situation",
            "content": situation,
            "timestamp": situation_timestamp,
            "token_count": situation_tokens,
        }, {
            "role": "system",
            "name": "information",
            "content": about_content,
            "timestamp": situation_timestamp,
            "token_count": about_tokens,
        }
    ], filtered_entries)
}
"""