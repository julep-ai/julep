"""Load a dotctx directory into a Brain and run it on a real provider.

A *dotctx* is a directory that describes one model call: a ``settings.yaml`` plus
a system-prompt file and an optional reply schema (see
``examples/dotctx/ticket_triage/``). ``load_dotctx`` reads that layout into a
:class:`Brain` (registered by name); ``brain_to_flow`` lowers the brain's round
policy to an execution shape (single ``think`` -> Pipeline, bounded ``max_rounds``
-> Feedback, ``agent: true`` -> Agent).

This example loads the bundled ``ticket_triage`` dotctx and runs it through the
any-llm-backed ``LlmCaller`` (``make_llm_caller``), so the ``provider:model`` named
in ``settings.yaml`` drives the call on whichever provider you point it at. The
brain carries its own system prompt and reply schema, so a single call returns a
structured classification.

Prereqs:

    pip install 'composable-agents[providers]' 'any-llm-sdk[anthropic]'
    export ANTHROPIC_API_KEY=sk-ant-...   # or the key for whatever provider the
                                          # settings.yaml ``model:`` names

Then:

    python examples/dotctx_triage.py

With no key set it still prints the loaded brain and its lowered shape, then skips
the live call, so it is a clean no-op.
"""

from __future__ import annotations

import asyncio
import os

from composable_agents.dotctx import Brain, brain_to_flow, load_dotctx
from composable_agents.execution.llm import DEFAULT_PROVIDER, make_llm_caller

HERE = os.path.dirname(os.path.abspath(__file__))
DOTCTX_DIR = os.path.join(HERE, "dotctx", "ticket_triage")

TICKET = (
    "I was charged twice for my subscription this month and now I can't log in. "
    "Please refund the duplicate charge and restore my access."
)


def _key_env(model: str) -> str:
    """The env var any-llm expects for this model's provider (e.g. OPENAI_API_KEY)."""
    provider = model.split(":", 1)[0] if ":" in model else DEFAULT_PROVIDER
    return f"{provider.upper()}_API_KEY"


def _shape_label(brain: Brain) -> str:
    """The execution shape a brain's round policy lowers to (mirrors brain_to_flow)."""
    if brain.sub_contract is not None:
        return "Staged (sub / child workflow)"
    if brain.is_agent or (brain.max_rounds is not None and brain.max_rounds <= 0):
        return "Agent (open-ended app loop)"
    if brain.max_rounds is not None and brain.max_rounds >= 1:
        return "Feedback (bounded iter_up_to)"
    return "Pipeline (single think)"


async def main() -> None:
    # Directory -> Brain. The brain is registered under its `name`, and its
    # system prompt + reply schema are read from the files settings.yaml names.
    brain = load_dotctx(DOTCTX_DIR)

    # Round policy -> IR shape (the defining move of a dotctx). No execution here;
    # this just shows which shape the framework would build for this brain.
    flow = brain_to_flow(brain)

    print(f"loaded dotctx: {os.path.relpath(DOTCTX_DIR, HERE)}")
    print(f"  brain name: {brain.name}")
    print(f"  model:      {brain.model}")
    print(f"  shape:      {_shape_label(brain)} [op={getattr(flow.op, 'name', flow.op)}]")
    print(f"  reply keys: {list((brain.reply_schema or {}).get('properties', {}))}")

    key_env = _key_env(brain.model)
    if not os.environ.get(key_env):
        print(f"\n- {key_env} not set; skipping the live call. Set it (or edit "
              "settings.yaml `model:`) to run the triage.")
        return

    # The activity-seam LlmCaller takes the Brain directly: it reads the brain's
    # model (routing the provider), system prompt, and reply schema, and returns
    # the parsed structured reply.
    caller = make_llm_caller()
    reply = await caller(brain, TICKET)

    print("\nticket:")
    print(f"  {TICKET}")
    print("triage:")
    print(f"  {reply}")


if __name__ == "__main__":
    asyncio.run(main())
