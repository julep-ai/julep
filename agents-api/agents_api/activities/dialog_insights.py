from textwrap import dedent
from typing import Callable

from temporalio import activity

from agents_api.clients import litellm

from .types import ChatML, DialogInsightsTaskArgs


def make_prompt(
    args: DialogInsightsTaskArgs,
    max_turns: int = 20,
):
    # Unpack
    dialog = args.dialog
    person1 = args.person1
    person2 = args.person2

    # Template
    template = dedent(
        """\
    [[Conversation]]
    {dialog_context}

    ---
    
    Write down if there are any details from the conversation above that {person1} might have found interesting from {person2}'s perspective, in a full sentence. Write down point by point only the most important points. Answer must be in third person.

    Answer: "
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
        person1=person1,
        person2=person2,
    )

    return prompt


async def run_prompt(
    dialog: list[ChatML],
    person1: str,
    person2: str,
    model: str = "gpt-4o",
    max_tokens: int = 400,
    temperature: float = 0.4,
    parser: Callable[[str], str] = lambda x: x,
) -> str:
    prompt = make_prompt(
        DialogInsightsTaskArgs(dialog=dialog, person1=person1, person2=person2)
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
async def dialog_insights(dialog: list[ChatML], person1: str, person2: str) -> None:
    # session_id = UUID(session_id)
    # entries = [
    #     Entry(**row)
    #     for _, row in client.run(
    #         get_toplevel_entries_query(session_id=session_id)
    #     ).iterrows()
    # ]

    # assert len(entries) > 0, "no need to summarize on empty entries list"

    await run_prompt(dialog, person1, person2)

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
