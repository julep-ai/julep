from textwrap import dedent
from typing import Callable

from temporalio import activity

from agents_api.clients import litellm

from .types import MemoryDensityTaskArgs


def make_prompt(args: MemoryDensityTaskArgs):
    # Unpack
    memory = args.memory

    # Template
    template = dedent(
        """\
    [[Memory from a Dialog]]
    {memory}

    [[Instruction]]
    You will generate increasingly concise, entity-dense summaries of the above Memory.
    
    Repeat the following 2 steps 5 times.
    
    Step 1: Identify 1-3 informative Entities (";" delimited) from the Memory which are missing from the previously generated summary.
    Step 2: Write a new, denser summary of identical length which covers every entity and detail from the previous summary plus the Missing Entities.
    
    A Missing Entity is: 
    - Relevant: to the main story.
    - Specific: descriptive yet concise (5 words or fewer).
    - Novel: not in the previous summary.
    - Faithful: present in the Memory.
    - Anywhere: located anywhere in the Memory.
    
    Guidelines:
    - The first summary should be long (4-5 sentences, ~80 words) yet highly non-specific, containing little information beyond the entities marked as missing. Use overly verbose language and fillers (e.g., "this article discusses") to reach ~80 words.
    - Make every word count: rewrite the previous summary to improve flow and make space for additional entities.
    - Make space with fusion, compression, and removal of uninformative phrases like "the memory discusses."
    - The summaries should become highly dense and concise yet self-contained, e.g., easily understood without the Memory.
    - Missing entities can appear anywhere in the new summary.
    - Never drop entities from the previous summary. If space cannot be made, add fewer new entities.
    
    Remember, use the exact same number of words for each summary.
    
    Answer in JSON. The JSON should be a list (length 5) of dictionaries whose keys are "Missing_Entities", "Denser_Summary" and "Density_Score" (between 1-10, higher is better).

    [[Result]]
    ```json
    """
    ).strip()

    prompt = template.format(memory=memory)

    return prompt


async def run_prompt(
    memory: str,
    model: str = "gpt-4o",
    max_tokens: int = 400,
    temperature: float = 0.2,
    parser: Callable[[str], str] = lambda x: x,
) -> str:
    prompt = make_prompt(MemoryDensityTaskArgs(memory=memory))

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
async def co_density(memory: str) -> None:
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
