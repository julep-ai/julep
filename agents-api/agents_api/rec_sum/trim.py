import json

from tenacity import retry, stop_after_attempt

from .data import trim_example_chat, trim_example_result
from .generate import generate
from .utils import add_indices, chatml, get_names_from_session

##########
## Trim ##
##########

trim_example_plan = """\
Thinking step by step:
- To trim the context, let's examine the messages in the session above.
- Messages 1, 2, and 3 are succinct and do not need trimming.
- However, messages 4, 5, and 6 are all rather verbose and can be safely trimmed.
- Message 7 is short enough and doesn't need any edits."""


trim_instructions = """\
Your goal is to identify messages in the session that are needlessly verbose and then trim them in length without losing any meaning or changing the tone of the message.

Instructions:
- Identify messages that are long and repetitive.
- Longer messages need to be converted into smaller, more compact version of them.
- Make sure to only trim out content that is not important to the context.
- Write down the trimmed messages as a json list along with their indices.
- Enclose your answer inside <ct:trimmed></ct:trimmed> XML tags.
- See the example to get a better idea of the task."""

# It is important to make keep the tone, setting and flow of the conversation consistent while trimming the messages.


def make_trim_prompt(session, user="a user", assistant="gpt-4-turbo", **_):
    return [
        f"You are given a session history of a chat between {user or 'a user'} and {assistant or 'gpt-4-turbo'}. The session is formatted in the ChatML JSON format (from OpenAI).\n\n{trim_instructions}\n\n<ct:example-session>\n{json.dumps(add_indices(trim_example_chat), indent=2)}\n</ct:example-session>\n\n<ct:example-plan>\n{trim_example_plan}\n</ct:example-plan>\n\n<ct:example-trimmed>\n{json.dumps(trim_example_result, indent=2)}\n</ct:example-trimmed>",
        f"Begin! Write the trimmed messages as a json list. First write your plan inside <ct:plan></ct:plan> and then your answer between <ct:trimmed></ct:trimmed>.\n\n<ct:session>\n{json.dumps(add_indices(session), indent=2)}\n\n</ct:session>",
    ]


@retry(stop=stop_after_attempt(2))
async def trim_messages(
    chat_session,
    model="gpt-4o",
    stop=["</ct:trimmed"],
    temperature=0.7,
    **kwargs,
):
    assert len(chat_session) >= 2, "Session is too short"

    names = get_names_from_session(chat_session)
    system_prompt, user_message = make_trim_prompt(chat_session, **names)
    messages = [chatml.system(system_prompt), chatml.user(user_message)]
    result = await generate(
        messages,
        model=model,
        stop=stop,
        temperature=temperature,
        **kwargs,
    )

    assert "<ct:trimmed>" in result["content"]
    trimmed_messages = json.loads(
        result["content"].split("<ct:trimmed>")[-1].replace("</ct:trimmed>", "").strip()
    )

    assert all((msg.get("index") is not None for msg in trimmed_messages))

    # Correct offset
    trimmed_messages = [{**msg, "index": msg["index"]} for msg in trimmed_messages]

    return trimmed_messages
