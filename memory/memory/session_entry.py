from typing import Optional

from memory.cozo import client
from memory.embed import embed
from memory.generate import generate
from memory.inserts import *
from memory.queries import *
from memory.updates import *
from memory.utils import *

max_tokens: int = 250
context_window: int = 2000

# 0. `samantha = get_character(samantha_character_id)`

samantha_character = (
    client.run(
        """
?[
    character_id,
    name,
    about,
    model,
] := *characters{
        character_id,
        name,
        about,
        model,
     },
     name = "Samantha",
     is_human = false,
"""
    )
    .iloc[0]
    .to_dict()
)


def make_entry(role: str, name: str, content: str):
    return dict(
        role=role,
        name=name,
        content=content,
    )


def make_situation(
    user_name: str, assistant_name: str, situation: str, add_time: bool = False
):
    # >  `make_situation = lambda data, add_time=False: (`
    # >  `  f"{samantha.name} is talking to {name}."`
    # >  `  + situation`
    # >  `  + f'\nIt is {human_now()}'`
    # >  `)`

    final_situation = (
        f"{assistant_name} is talking to {user_name}." + f" {situation.strip()}"
    )

    if add_time:
        final_situation += f"\n\nIt is {get_human_date_time()}"

    return final_situation


async def respond(
    email: str,
    vocode_conversation_id: str,
    name: Optional[str] = "Anonymous",
    user_input: Optional[str] = None,
    situation: Optional[str] = None,
    echo: bool = False,
):
    # 1. `assert situation ^ user_input`
    assert bool(user_input) or bool(
        situation
    ), "Must provide either user_input or situation"
    new_session = not bool(user_input)

    # 2. `user_data = get_user_by_email(email)`
    echo and print(f"Getting user data for {email}")
    user_data = get_user_by_email(email)

    # 3. `if not user_data:`
    #     - `character_data = create_character(name, about, assistant=samantha)`
    #     - `user_data = create_user(email, character_data)`
    if not user_data:
        assistant_name = user_data["assistant"]["name"]
        about = f"{name} is a guest user of Julep AI who is here to see what it's like to talk to {assistant_name}."

        # Create character
        echo and print(f"Creating character for {email}")
        character_data = create_character(name, is_human=True, about=about, model=None)
        character_id = character_data["character_id"]

        # Create user
        echo and print(f"Creating user for {email}")
        user_data = create_user(email, character_id, samantha_character["character_id"])

    character_id = user_data["character_id"]
    name = user_data["character"]["name"]
    about = user_data["character"]["about"]

    assistant_id = user_data["assistant_id"]
    assistant_name = user_data["assistant"]["name"]
    assistant_about = user_data["assistant"]["about"]

    # 4. `session = get_session(vocode_conversation_id)`
    echo and print(f"Getting session for {email}")
    session = get_session_by_email(email, vocode_conversation_id)

    # 5. `assert situation and not session`
    assert bool(situation) ^ bool(
        session
    ), "Can only provide either session or situation"

    # 6. `if not session:`
    #     - `session = create_session(user_data, vocode_conversation_id, situation)`
    #     - `add_session_characters(session, user_data)`
    if not session:
        echo and print(f"Creating session for {email}")
        session = create_session(email, vocode_conversation_id, situation)

    # 7. `entries = get_session_entries(session_id)`
    session_id = session["session_id"]
    echo and print(f"Getting session entries for {session_id}")

    entries = get_session_entries(session_id)

    # 8. `{summary} = session`
    summary = session["summary"]

    # 9. `situation_final = make_situation(user_data, add_time=True)`
    situation = situation or session["situation"]
    situation_final = make_situation(name, assistant_name, situation, add_time=True)
    situation_final = make_entry("system", "situation", situation_final)

    # 10.
    # >  `info_top = (`
    # >  `  samantha.about`
    # >  `  + user_data.about`
    # >  `  + f'{samantha.name} is very funny but also polite and keeps her responses brief.'`
    # >  `)`
    info_top = (
        samantha_character["about"]
        + f" {about}"
        + f"{assistant_name} should keep her responses crisp and brief."
    )

    info_top = make_entry("system", "information", info_top)

    # 11. `all_entries = situation_final + info_top + entries`
    all_entries = [situation_final, info_top] + entries
    user_input_entry = None

    if user_input:
        user_input_entry = make_entry(
            "user", name, user_input
        )
        all_entries.append(user_input_entry)

    # 13. `thought = generate_thought(truncated_entries)`
    echo and print(f"Generating thought for {email}")

    thought_max_tokens = 40

    situational_entries = truncate(
        all_entries,
        max_tokens=context_window - thought_max_tokens,
        #
        # Keep system entries at the beginning and last 3 entries only
        keep_when=lambda x, i: (x["role"] == "system" and i == 0)
        or (i > len(all_entries) - 3),
    )

    # TODO: Re-enable thoughts when they are working
    thought = ""
    
    if new_session:
        thought = f"The call is just starting. I should greet {name}!"
    #
    # else:

    #     thought_suffix = "<|section|>thought\n"
    #     thought = await generate(
    #         situational_entries,
    #         max_tokens=thought_max_tokens,
    #         temperature=0.0,
    #         frequency_penalty=0.0,
    #         presence_penalty=0.0,
    #         best_of=1,
    #         prompt_settings=dict(suffix=thought_suffix),
    #     )

    #     thought = thought["choices"]
    #     thought = thought[0]["text"] if thought else ""

    echo and print(f"Thought: `{thought}`")

    # 14. `beliefs = get_matching_beliefs(user_data, thought)`
    if thought:
        thought_entry = make_entry("system", "thought", thought)
        all_entries.append(thought_entry)

    echo and print(f"Fetching beliefs for {email}")

    beliefs = get_matching_beliefs(situational_entries)

    if beliefs:
        # 15. `all_entries.append(belief)`
        belief_entry = make_entry("system", "belief", " ".join(beliefs))
        all_entries.append(belief_entry)

    # 16. `truncated_entries = truncate(all_entries)`
    truncated_entries = truncate(all_entries, max_tokens=context_window - max_tokens)

    # TODO: Add summary
    # 17. `if len(truncated_entries) < len(all_entries) and summary:`
    #     - `truncated_entries.insert(summary, 3)`

    # 18. `assistant_output = generate(truncated_entries)`
    echo and print(f"Generating assistant output for {email}")

    utterance_suffix = f"<|section|>me ({assistant_name})\n"
    generated = await generate(
        truncated_entries,
        max_tokens=max_tokens,
        prompt_settings=dict(suffix=utterance_suffix),
    )

    generated = generated["choices"]
    assistant_output = ""

    if generated:
        assistant_output = generated[0]["text"]

        assistant_output_entry = make_entry(
            "assistant", assistant_name, assistant_output,
        )

        all_entries.append(assistant_output_entry)

    # 19. `return { assistant_output, session.session_id }`
    result = dict(
        assistant_output=assistant_output,
        session_id=session_id,
    )

    # Add entries to the session
    echo and print(f"Adding {len(all_entries)} session entries for {email}")
    add_entries(session["session_id"], all_entries)

    # TODO: background tasks
    # 21. (In the background)
    #     - `update_summary(session, truncated_entries[3:])`
    #     - `if new_session: add_episodes(session, situation)`
    #     - `add_episodes(session, truncated_entries)`

    return result, []
