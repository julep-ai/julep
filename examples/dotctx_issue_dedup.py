"""Inspect an agent-shaped issue-dedup dotctx without making a provider call.

This rich dotctx declares a bounded tool-using decision contract: it has
``max_rounds=4``, ``require_tool_call=true``, and a prompt that requires a
``search_similar_posts`` call before choosing ``create``. Its bounded round policy
lowers to Feedback rather than the open-ended Agent shape.

The current ``LlmCaller`` / ``complete_reasoner`` path runs only one structured
round. Native tool-calling and enforcement of reasoner loops arrive in Phase 3/4, so
running that single round would bypass the mandatory search and misrepresent the
decision. This driver intentionally does not run it: it is a keyless, no-op view of
the declared contract, with no API key, network, Temporal, clock, or randomness.
"""

from __future__ import annotations

import asyncio
import os

from julep.dotctx import Reasoner, load_dotctx, reasoner_to_flow

HERE = os.path.dirname(os.path.abspath(__file__))
DOTCTX_DIR = os.path.join(HERE, "dotctx", "issue_dedup")


def _shape_label(reasoner: Reasoner) -> str:
    """The execution shape a reasoner's round policy lowers to."""
    if reasoner.sub_contract is not None:
        return "Staged (sub / child workflow)"
    if reasoner.is_agent or (
        reasoner.max_rounds is not None and reasoner.max_rounds <= 0
    ):
        return "Agent (open-ended app loop)"
    if reasoner.max_rounds is not None and reasoner.max_rounds >= 1:
        return "Feedback (bounded iter_up_to)"
    return "Pipeline (single think)"


async def main() -> None:
    """Load and lower the contract; do not fake its not-yet-native tool loop."""
    reasoner = load_dotctx(DOTCTX_DIR)
    flow = reasoner_to_flow(reasoner)
    schema = reasoner.reply_schema or {}

    print(f"loaded dotctx: {os.path.relpath(DOTCTX_DIR, HERE)}")
    print(f"  reasoner name:      {reasoner.name}")
    print(f"  model:              {reasoner.model}")
    print(f"  temperature:        {reasoner.temperature}")
    print(f"  max_rounds:         {reasoner.max_rounds}")
    print(
        f"  shape:              {_shape_label(reasoner)} "
        f"[op={getattr(flow.op, 'name', flow.op)}]"
    )
    print(f"  granted tools:      {reasoner.tools}")
    print(f"  require_tool_call:  {reasoner.require_tool_call}")
    print(f"  reply-schema keys:  {list(schema.get('properties', {}))}")
    print("\nThis is intentionally a keyless no-op; no provider call is made.")
    print(
        "LlmCaller (complete_reasoner) currently runs one structured round, but this "
        "contract requires a bounded tool-using loop: max_rounds=4, "
        "require_tool_call=true, and a mandatory search_similar_posts call before "
        "choosing create. Running one round would bypass that search and misrepresent "
        "the decision. Tool-loop execution and enforcement land in Phase 3/4."
    )
    return None


if __name__ == "__main__":
    asyncio.run(main())
