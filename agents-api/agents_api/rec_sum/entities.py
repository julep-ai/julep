import json
from typing import Any

import pandas as pd
from tenacity import retry, stop_after_attempt

from .data import entities_example_chat
from .generate import generate
from .utils import chatml, get_names_from_session

##############
## Entities ##
##############

entities_example_plan = """\
Thinking step by step:
- To add context for future entries, let's outline the main entities in the session above.
- In this session, as mentioned in the first message metadata, the user's name is Camille and the assistant's name is JaneBot.
- They talk about Elon Musk and the banana tattoo on Camille's arm briefly."""


entities_example_result = """\
1. Camille (The user): Humorous, creative, and enjoys playful banter.
2. JaneBot (The assistant): Engages in lighthearted conversation and tries to guess user's thoughts.
3. Elon Musk: Camille and JaneBot discuss the polarizing tech and space industry figure.
4. Banana Tattoo: Camille has a tattoo of a banana on their arm."""


entities_instructions = """\
Your goal is to identify the main entities in the session. Entities should include:
- Characters in the conversation: Assistant, User1, User2
- People references or spoken about
- Objects discussed about
- Places of interest
- ...etc

Instructions:
- Identify and extract important entities discussed.
- You can add entities that, while not directly mentioned, are important in the context of the conversation.
- Write a brief line to provide context about each entity explaining it's relevance to the conversation.
- Enclose your answer inside <ct:entities></ct:entities> XML tags.
- See the example to get a better idea of the task."""


def make_entities_prompt(
    session: list[pd.Series] | list[Any], user="a user", assistant="gpt-4-turbo", **_
):
    session = [m.to_dict() if isinstance(m, pd.Series) else m for m in session]
    session_json_str = json.dumps(session, indent=2)

    return [
        f"You are given a session history of a chat between {user or 'a user'} and {assistant or 'gpt-4-turbo'}. The session is formatted in the ChatML JSON format (from OpenAI).\n\n{entities_instructions}\n\n<ct:example-session>\n{json.dumps(entities_example_chat, indent=2)}\n</ct:example-session>\n\n<ct:example-plan>\n{entities_example_plan}\n</ct:example-plan>\n\n<ct:example-entities>\n{entities_example_result}\n</ct:example-entities>",
        f"Begin! Write the entities as a Markdown formatted list. First write your plan inside <ct:plan></ct:plan> and then the extracted entities between <ct:entities></ct:entities>.\n\n<ct:session>\n{session_json_str}\n\n</ct:session>",
    ]


@retry(stop=stop_after_attempt(2))
async def get_entities(
    chat_session,
    model="gpt-4-turbo",
    stop=["</ct:entities"],
    temperature=0.7,
    **kwargs,
):
    assert len(chat_session) >= 2, "Session is too short"

    names = get_names_from_session(chat_session)
    system_prompt, user_message = make_entities_prompt(chat_session, **names)
    messages = [chatml.system(system_prompt), chatml.user(user_message)]
    result = await generate(
        messages,
        model=model,
        stop=stop,
        temperature=temperature,
        **kwargs,
    )

    assert "<ct:entities>" in result["content"]
    result["content"] = (
        result["content"]
        .split("<ct:entities>")[-1]
        .replace("</ct:entities>", "")
        .strip()
    )
    result["role"] = "system"
    result["name"] = "entities"

    return chatml.make(**result)
