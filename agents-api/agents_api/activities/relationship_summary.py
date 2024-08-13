from textwrap import dedent
from typing import Callable

from temporalio import activity

from ..clients import litellm
from .types import RelationshipSummaryTaskArgs


def make_prompt(args: RelationshipSummaryTaskArgs):
    # Unpack
    statements = args.statements
    person1 = args.person1
    person2 = args.person2

    # Template
    template = dedent(
        """\
    Statements:
    - {statements_joined}
    
    Based on the statements above, summarize {person1} and {person2}'s relationship in a 2-3 sentences. What do they feel or know about each other?
    
    Answer: "
    """
    ).strip()

    prompt = template.format(
        statements_joined="\n- ".join(statements),
        person1=person1,
        person2=person2,
    )

    return prompt


async def run_prompt(
    statements: list[str],
    person1: str,
    person2: str,
    model: str = "gpt-4o",
    max_tokens: int = 400,
    temperature: float = 0.6,
    parser: Callable[[str], str] = lambda x: x,
) -> str:
    prompt = make_prompt(
        RelationshipSummaryTaskArgs(
            statements=statements, person1=person1, person2=person2
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
async def relationship_summary(
    statements: list[str], person1: str, person2: str
) -> None:
    # session_id = UUID(session_id)
    # entries = [
    #     Entry(**row)
    #     for _, row in client.run(
    #         get_toplevel_entries_query(session_id=session_id)
    #     ).iterrows()
    # ]

    # assert len(entries) > 0, "no need to summarize on empty entries list"

    await run_prompt(statements=statements, person1=person1, person2=person2)

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
