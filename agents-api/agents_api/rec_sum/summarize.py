import json
from typing import List

from tenacity import retry, stop_after_attempt

from .data import summarize_example_chat, summarize_example_result
from .generate import generate
from .utils import add_indices, chatml, get_names_from_session

##########
## summarize ##
##########

summarize_example_plan: str = """\
Planning step by step:
- We can replace entries 1,2,3,4 with a summary of those messages.
- We can replace entries 5,6,7,8 similarly.
- It could be disruptive to remove messages 9-16 because that might lose the joke's context.
- We can safely summarize entries 17,18 without losing context.
- We should keep 21 because it's given by the user and they might ask about it again.
- We should keep the assistant's response in message 22 to keep the context.
- Messages 23-32 are repetitive and can be summarized.
- We should retain message 33 since it's a direct request from the user.
- We can safely summarize message 34's essay into just the salient points only."""


summarize_instructions: str = """\
Your goal is to compactify the history by coalescing redundant information in messages into their summary in order to reduce its size and save costs.

Instructions:
- Combine multiple messages into summaries when possible as long as that doesn't disrupt the structure of the session.
- You can convert large messages (such as an essay) into a list of points.
- Do not summarize content that the user shared since it might be relevant to future messages.
- Make sure to preserve the tone of the conversation and its flow. Refer to the example and do EXACTLY as shown.
- VERY IMPORTANT: Add the indices of messages that are being summarized so that those messages can then be removed from the session otherwise, there'll be no way to identify which messages to remove. See example for more details."""


def make_summarize_prompt(
    session, user="a user", assistant="gpt-4-turbo", **_
) -> List[str]:
    return [
        f"You are given a session history of a chat between {user or 'a user'} and {assistant or 'gpt-4-turbo'}. The session is formatted in the ChatML JSON format (from OpenAI).\n\n{summarize_instructions}\n\n<ct:example-session>\n{json.dumps(add_indices(summarize_example_chat), indent=2)}\n</ct:example-session>\n\n<ct:example-plan>\n{summarize_example_plan}\n</ct:example-plan>\n\n<ct:example-summarized-messages>\n{json.dumps(summarize_example_result, indent=2)}\n</ct:example-summarized-messages>",
        f"Begin! Write the summarized messages as a json list just like the example above. First write your plan inside <ct:plan></ct:plan> and then your answer between <ct:summarized-messages></ct:summarized-messages>. Don't forget to add the indices of the messages being summarized alongside each summary.\n\n<ct:session>\n{json.dumps(add_indices(session), indent=2)}\n\n</ct:session>",
    ]


@retry(stop=stop_after_attempt(2))
async def summarize_messages(
    chat_session,
    model="gpt-4o",
    stop=["</ct:summarized"],
    temperature=0.8,
    **kwargs,
):
    assert len(chat_session) >= 2, "Session is too short"

    offset = 0

    # Remove the system prompt if present
    if (
        chat_session[0]["role"] == "system"
        and chat_session[0].get("name") != "entities"
    ):
        chat_session = chat_session[1:]

        # The indices are not matched up correctly
        offset = 1

    names = get_names_from_session(chat_session)
    system_prompt, user_message = make_summarize_prompt(chat_session, **names)
    messages = [chatml.system(system_prompt), chatml.user(user_message)]
    result = await generate(
        messages,
        model=model,
        stop=stop,
        temperature=temperature,
        **kwargs,
    )

    assert "<ct:summarized-messages>" in result["content"]
    summarized_messages = json.loads(
        result["content"]
        .split("<ct:summarized-messages>")[-1]
        .replace("</ct:summarized-messages>", "")
        .strip()
    )

    assert all((msg.get("summarizes") is not None for msg in summarized_messages))

    # Correct offset
    summarized_messages = [
        {**msg, "summarizes": [i + offset for i in msg["summarizes"]]}
        for msg in summarized_messages
    ]

    return summarized_messages
