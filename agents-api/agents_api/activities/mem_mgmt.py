from textwrap import dedent
from typing import Callable
from uuid import UUID

from beartype import beartype
from temporalio import activity

from ..autogen.openapi_model import InputChatMLMessage
from ..clients import litellm
from .types import MemoryManagementTaskArgs

example_previous_memory = """
Speaker 1: Composes and listens to music. Likes to buy basketball shoes but doesn't wear them often.
""".strip()

example_dialog_context = """
Speaker 1: Did you find a place to donate your shoes?
Speaker 2: I did!  I was driving to the grocery store the other day, when I noticed a bin labeled "Donation for Shoes and Clothing."  It was easier than I thought!  How about you?  Why do you have so many pairs of sandals?
Speaker 1: I don't understand myself! When I look them online I just have the urge to buy them, even when I know I don't need them. This addiction is getting worse and worse.
Speaker 2: I completely agree that buying shoes can become an addiction!  Are there any ways you can make money from home while waiting for a job offer from a call center?
Speaker 1: Well I already got the job so I just need to learn using the software. When I was still searching for jobs, we actually do a yard sale to sell many of my random items that are never used and clearly aren't needed either.
Speaker 2: Congratulations on getting the job!  I know it'll help you out so much.  And of course, maybe I should turn to yard sales as well, for they can be a great way to make some extra cash!
Speaker 1: Do you have another job or do you compose music for a living? How does your shopping addiction go?
Speaker 2: As a matter of fact, I do have another job in addition to composing music.  I'm actually a music teacher at a private school, and on the side, I compose music for friends and family.  As far as my shopping addiction goes, it's getting better.  I promised myself that I wouldn't buy myself any more shoes this year!
Speaker 1: Ah, I remember the time I promised myself the same thing on not buying random things anymore, never work so far. Good luck with yours!
Speaker 2: Thanks!  I need the good luck wishes.  I've been avoiding malls and shopping outlets.  Maybe you can try the same!
Speaker 1: I can avoid them physically, but with my job enable me sitting in front of my computer for a long period of time, I already turn the shopping addiction into online-shopping addiction. lol. Wish me luck!
Speaker 2: Sure thing!  You know, and speaking of spending time before a computer, I need to look up information about Precious Moments figurines.  I'd still like to know what they are!
""".strip()

example_updated_memory = """
Speaker 1:
- Enjoys composing and listening to music.
- Recently got a job that requires the use of specialized software.
- Displays a shopping addiction, particularly for shoes, that has transitioned to online-shopping due to job nature.
- Previously attempted to mitigate shopping addiction without success.
- Had organized a yard sale to sell unused items when job searching.

Speaker 2:
- Also enjoys buying shoes and admits to it being addictive.
- Works as a music teacher at a private school in addition to composing music.
- Takes active measures to control his shopping addiction, including avoiding malls.
- Is interested in Precious Moments figurines.
""".strip()


def make_prompt(
    args: MemoryManagementTaskArgs,
    max_turns: int = 10,
    num_sentences: int = 10,
):
    # Unpack
    dialog = args.dialog
    previous_memories = args.previous_memories

    # Template
    template = dedent(
        """\
    **Instructions**
    You are an advanced AI language model with the ability to store and update a memory to keep track of key personality information for people. You will receive a memory and a dialogue between two people.
    
    Your goal is to update the memory by incorporating the new personality information for both participants while ensuring that the memory does not exceed {num_sentences} sentences.
    
    To successfully update the memory, follow these steps:
    
    1. Carefully analyze the existing memory and extract the key personality information of the participants from it.
    2. Consider the dialogue provided to identify any new or changed personality traits of either participant that need to be incorporated into the memory.
    3. Combine the old and new personality information to create an updated representation of the participants' traits.
    4. Structure the updated memory in a clear and concise manner, ensuring that it does not exceed {num_sentences} sentences.
    5. Pay attention to the relevance and importance of the personality information, focusing on capturing the most significant aspects while maintaining the overall coherence of the memory.
    
    Remember, the memory should serve as a reference point to maintain continuity in the dialogue and help accurately set context in future conversations based on the personality traits of the participants.
    
    **Test Example**
    [[Previous Memory]]
    {example_previous_memory}
    
    [[Dialogue Context]]
    {example_dialog_context}
    
    [[Updated Memory]]
    {example_updated_memory}
    
    **Actual Run**
    [[Previous Memory]]
    {previous_memory}
    
    [[Dialogue Context]]
    {dialog_context}
    
    [[Updated Memory]]
    """
    ).strip()

    # Filter dialog (keep only user and assistant sections)
    dialog = [entry for entry in dialog if entry.role != "system"]

    # Truncate to max_turns
    dialog = dialog[-max_turns:]

    # Prepare dialog context
    dialog_context = "\n".join(
        [
            f'{e.name or ("User" if e.role == "user" else "Assistant")}: {e.content}'
            for e in dialog
        ]
    )

    prompt = template.format(
        dialog_context=dialog_context,
        previous_memory="\n".join(previous_memories),
        num_sentences=num_sentences,
        example_dialog_context=example_dialog_context,
        example_previous_memory=example_previous_memory,
        example_updated_memory=example_updated_memory,
    )

    return prompt


async def run_prompt(
    dialog: list[InputChatMLMessage],
    session_id: UUID,
    previous_memories: list[str] = [],
    model: str = "gpt-4o",
    max_tokens: int = 400,
    temperature: float = 0.4,
    parser: Callable[[str], str] = lambda x: x,
) -> str:
    prompt = make_prompt(
        MemoryManagementTaskArgs(
            session_id=session_id,
            model=model,
            dialog=dialog,
            previous_memories=previous_memories,
        )
    )

    response = await litellm.acompletion(
        model=model,
        messages=[
            {
                "content": prompt,
                "role": "user",
            }
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        stop=["<", "<|"],
        stream=False,
    )

    content = response.choices[0].message.content

    return parser(content.strip() if content is not None else "")


@activity.defn
@beartype
async def mem_mgmt(
    dialog: list[InputChatMLMessage],
    session_id: UUID,
    previous_memories: list[str] = [],
) -> None:
    # session_id = UUID(session_id)
    # entries = [
    #     Entry(**row)
    #     for _, row in client.run(
    #         get_toplevel_entries_query(session_id=session_id)
    #     ).iterrows()
    # ]

    # assert len(entries) > 0, "no need to summarize on empty entries list"

    await run_prompt(dialog, session_id, previous_memories)

    # new_entry = Entry(
    #     session_id=session_id,
    #     source="summarizer",
    #     role="system",
    #     name="information",
    #     content=response,
    #     timestamp=entries[-1].timestamp + 0.01,
    # )

    # client.run(
    #     entries_summarization_query(
    #         session_id=session_id,
    #         new_entry=new_entry,
    #         old_entry_ids=[e.id for e in entries],
    #     )
    # )
