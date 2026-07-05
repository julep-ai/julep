"""Load a dotctx directory into a Reasoner and run it on a real provider.

A *dotctx* is a directory that describes one model call: a ``settings.yaml`` plus
a system-prompt file and an optional reply schema (see
``examples/dotctx/ticket_triage/``). ``load_dotctx`` reads that layout into a
:class:`Reasoner` (registered by name); ``reasoner_to_flow`` lowers the reasoner's round
policy to an execution shape (single ``think`` -> Pipeline, bounded ``max_rounds``
-> Feedback, ``agent: true`` -> Agent).

This example loads the bundled ``ticket_triage`` dotctx and runs it through the
any-llm-backed ``LlmCaller`` (``make_llm_caller``), so the ``provider:model`` named
in ``settings.yaml`` drives the call on whichever provider you point it at. The
reasoner carries its own system prompt and reply schema, so a single call returns a
structured classification.

Prereqs:

    pip install 'julep[providers]' 'any-llm-sdk[anthropic]'
    export ANTHROPIC_API_KEY=sk-ant-...   # or the key for whatever provider the
                                          # settings.yaml ``model:`` names

Then:

    python examples/dotctx_triage.py

With no key set it still prints the loaded reasoner and its lowered shape, then skips
the live call, so it is a clean no-op.
"""

from __future__ import annotations

import asyncio
import os

from julep.dotctx import Reasoner, reasoner_to_flow, load_dotctx
from julep.execution.llm import DEFAULT_PROVIDER, make_llm_caller

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


def _shape_label(reasoner: Reasoner) -> str:
    """The execution shape a reasoner's round policy lowers to (mirrors reasoner_to_flow)."""
    if reasoner.sub_contract is not None:
        return "Staged (sub / child workflow)"
    if reasoner.is_agent or (reasoner.max_rounds is not None and reasoner.max_rounds <= 0):
        return "Agent (open-ended app loop)"
    if reasoner.max_rounds is not None and reasoner.max_rounds >= 1:
        return "Feedback (bounded iter_up_to)"
    return "Pipeline (single think)"


async def main() -> None:
    # Directory -> Reasoner. The reasoner is registered under its `name`, and its
    # system prompt + reply schema are read from the files settings.yaml names.
    reasoner = load_dotctx(DOTCTX_DIR)

    # Round policy -> IR shape (the defining move of a dotctx). No execution here;
    # this just shows which shape the framework would build for this reasoner.
    flow = reasoner_to_flow(reasoner)

    print(f"loaded dotctx: {os.path.relpath(DOTCTX_DIR, HERE)}")
    print(f"  reasoner name: {reasoner.name}")
    print(f"  model:      {reasoner.model}")
    print(f"  shape:      {_shape_label(reasoner)} [op={getattr(flow.op, 'name', flow.op)}]")
    print(f"  reply keys: {list((reasoner.reply_schema or {}).get('properties', {}))}")

    key_env = _key_env(reasoner.model)
    if not os.environ.get(key_env):
        print(f"\n- {key_env} not set; skipping the live call. Set it (or edit "
              "settings.yaml `model:`) to run the triage.")
        return

    # The activity-seam LlmCaller takes the Reasoner directly: it reads the reasoner's
    # model (routing the provider), system prompt, and reply schema, and returns
    # the parsed structured reply.
    caller = make_llm_caller()
    reply = await caller(reasoner, TICKET)

    print("\nticket:")
    print(f"  {TICKET}")
    print("triage:")
    print(f"  {reply}")


if __name__ == "__main__":
    asyncio.run(main())
