from textwrap import dedent
from typing import Callable

from temporalio import activity

from ..clients import litellm
from .types import SalientQuestionsTaskArgs


def make_prompt(args: SalientQuestionsTaskArgs):
    # Unpack
    statements = args.statements
    num = args.num

    # Template
    template = dedent(
        """\
    Statements:
    - {statements_joined}
    
    Given only the information above, what are the {num} most salient high-level questions we can answer about the subjects grounded in the statements?
    - """
    ).strip()

    prompt = template.format(
        statements_joined="\n- ".join(statements),
        num=num,
    )

    return prompt


async def run_prompt(
    statements: list[str],
    num: int = 3,
    model: str = "gpt-4o",
    max_tokens: int = 400,
    temperature: float = 0.6,
    parser: Callable[[str], str] = lambda x: x,
) -> str:
    prompt = make_prompt(SalientQuestionsTaskArgs(statements=statements, num=num))

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
async def salient_questions(statements: list[str], num: int = 3) -> None:
    # session_id = UUID(session_id)
    # entries = [
    #     Entry(**row)
    #     for _, row in client.run(
    #         get_toplevel_entries_query(session_id=session_id)
    #     ).iterrows()
    # ]

    # assert len(entries) > 0, "no need to summarize on empty entries list"

    await run_prompt(statements=statements, num=num)

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
