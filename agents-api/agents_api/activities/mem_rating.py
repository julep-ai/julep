from textwrap import dedent
from typing import Callable

from temporalio import activity

from ..clients import litellm
from .types import MemoryRatingTaskArgs


def make_prompt(args: MemoryRatingTaskArgs):
    # Unpack
    memory = args.memory

    # Template
    template = dedent(
        """\
    Importance distinguishes mundane from core memories, by assigning a higher score to those memory objects that the agent believes to be important. For instance, a mundane event such as eating breakfast in one’s room would yield a low importance score, whereas a breakup with one’s significant other would yield a high score. There are again many possible implementations of an importance score; we find that directly asking the language model to output an integer score is effective.
    
    On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following piece of memory.
    
    [[Format to follow]]
    Memory: <given memory>
    Thought: <fill in your reasoning>
    Rating: <fill in a number between 0-10>
    
    [[Hypothetical Example]]
    Memory: buying groceries at The Willows Market and Pharmacy
    Thought: Grocery shopping is a routine task that most people engage in regularly. While there may be some significance attached to it—for instance, if it's part of a new diet plan or if you're buying groceries for a special occasion—in general, it is unlikely to be a memory that carries substantial emotional weight or has a long-lasting impact on one's life. However, there can be some variance; a mundane grocery trip could become more important if you bump into an old friend or make a particularly interesting discovery (e.g., a new favorite food). But in the absence of such circumstances, the poignancy would be quite low.
    Rating: 2
    
    [[Actual run]]
    Memory: {memory}
    """
    ).strip()

    prompt = template.format(memory=memory)

    return prompt


async def run_prompt(
    memory: str,
    model: str = "gpt-4o",
    max_tokens: int = 400,
    temperature: float = 0.1,
    parser: Callable[[str], str] = lambda x: x,
) -> str:
    prompt = make_prompt(MemoryRatingTaskArgs(memory=memory))

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
async def mem_rating(memory: str) -> None:
    # session_id = UUID(session_id)
    # entries = [
    #     Entry(**row)
    #     for _, row in client.run(
    #         get_toplevel_entries_query(session_id=session_id)
    #     ).iterrows()
    # ]

    # assert len(entries) > 0, "no need to summarize on empty entries list"

    await run_prompt(memory=memory)

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
