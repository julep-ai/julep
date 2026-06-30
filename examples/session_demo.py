"""Long-lived, STATEFUL conversational session against a REAL provider.

One driver, three backends:

    python examples/session_demo.py local
    python examples/session_demo.py temporal
    python examples/session_demo.py cma

Each backend opens a live session and drives a scripted 2-turn conversation that
PROVES statefulness: turn 1 plants a codeword ("Remember the codeword is
BANANA."), turn 2 asks for it back ("What is the codeword?"). The reply to turn 2
is produced by a REAL ``anthropic:claude-haiku-4-5-20251001`` call; if it contains
BANANA, the carrier threaded the prior turn across the session and we print
``STATEFUL_RECALL=yes``.

How each backend threads state (this is the interesting part):

* local / temporal -- the session turn body is real framework IR:
      scan( seq( recv("in"),
                 par( seq(arr(prep), think(REASONER)),  # REAL anthropic call
                      ident() ),                         # keep recv output alive
                 arr(post) ),                            # -> (next_carrier, reply)
            init=[] )
  ``recv`` yields ``{"carrier": history, "msg": user_msg}``; ``prep`` renders the
  whole conversation as the model prompt; ``think`` makes the live call; ``post``
  appends (user, assistant) to the history and returns ``(new_history, reply)``.
  The LOOP's ``split`` flag splits that 2-tuple into the next carrier + the emit.
  The carrier (the conversation transcript) is the proof of statefulness: it is
  what the framework threads turn-to-turn, and it is what feeds the turn-2 prompt.
    - local   : LocalSessionHandle.open(reasoners={REASONER: <live caller>})
    - temporal: a real worker (SessionWorkflow + activities + a REAL LlmCaller)
                on Temporal's time-skipping test server; Agent.open(backend=...).

* cma -- the hosted Claude Managed Agents backend (CMASessionHandle) creates one
  fresh hosted session per inbound turn and does NOT thread a carrier between
  turns (it ignores the session IR body). So statefulness cannot be threaded by
  the framework here; instead the DRIVER threads it: each message we send carries
  the full running transcript, so the hosted model still sees turn 1 when it
  answers turn 2. The recall proof holds; the threading seam differs. (Caveat
  surfaced explicitly in the output.)

Prereqs:

    set -a; source .env; set +a              # ANTHROPIC_API_KEY (not shell-exported)
    uv run --extra dev --extra providers [--extra cma] python examples/session_demo.py <backend>

Cost is real provider spend; each run is 2 short Haiku calls per backend.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from typing import Any

from composable_agents import (
    Agent,
    Reasoner,
    SessionEvent,
    arr,
    ident,
    par,
    recv,
    register_pure,
    scan,
    seq,
    think,
)
from composable_agents.dotctx import get_reasoner
from composable_agents.execution.llm import complete_reasoner
from composable_agents.registry import DEFAULT_REGISTRY

MODEL = "anthropic:claude-haiku-4-5-20251001"
REASONER = "session_demo.assistant"
CODEWORD = "BANANA"

SYSTEM = (
    "You are a concise, stateful conversational assistant. You are given the "
    "full conversation so far as a JSON list of {role, content} messages. Reply "
    "with a single short sentence answering the latest user message, using the "
    "earlier turns as memory. Reply with plain text only (no JSON, no preamble)."
)

SCRIPT = [
    f"Remember the codeword is {CODEWORD}. Just acknowledge.",
    "What is the codeword? Answer with just the word.",
]


# --------------------------------------------------------------------------- #
# Registered reasoner: a real Anthropic call, NO reply_schema => free text.
# Registered once at import so both the local caller and the Temporal worker
# (same process) resolve it from the global registry.
# --------------------------------------------------------------------------- #
DEFAULT_REGISTRY.register_reasoner(
    Reasoner(
        name=REASONER,
        model=MODEL,
        system=SYSTEM,
        max_tokens=64,
    )
)


# --------------------------------------------------------------------------- #
# Pure turn helpers (deterministic; safe inside the Temporal sandbox). Registered
# so frozen ``arr`` leaves resolve in-process and on the worker.
# --------------------------------------------------------------------------- #
def _prep(value: dict[str, Any]) -> list[dict[str, str]]:
    """recv output -> the message list the reasoner renders as its prompt.

    ``value`` is ``{"carrier": history, "msg": user_msg}``. The reasoner sees the
    whole transcript (prior turns + this user turn), which is exactly how the
    carrier proves statefulness: turn 2's prompt contains turn 1.
    """
    history = list(value.get("carrier") or [])
    msg = value["msg"]
    return [*history, {"role": "user", "content": str(msg)}]


def _post(pair: list[Any]) -> tuple[list[dict[str, str]], str]:
    """[reply_text, recv_output] -> (next_carrier, emitted_reply).

    ``par`` merges branch values positionally: branch 0 is the reasoner reply,
    branch 1 is the untouched recv output (so we recover the prior history + msg
    that ``think`` would otherwise have discarded).
    """
    reply, recv_out = pair[0], pair[1]
    reply_text = reply if isinstance(reply, str) else str(reply)
    history = list(recv_out.get("carrier") or [])
    msg = recv_out["msg"]
    next_history = [
        *history,
        {"role": "user", "content": str(msg)},
        {"role": "assistant", "content": reply_text},
    ]
    return next_history, reply_text


register_pure("session_demo.prep", _prep)
register_pure("session_demo.post", _post)


def build_session():
    """The stateful turn body, as framework IR (local + temporal backends)."""
    turn = seq(
        recv("in"),
        par(seq(arr("session_demo.prep"), think(REASONER)), ident()),
        arr("session_demo.post"),
    )
    return scan(turn, init=[], in_channel="in", out_channel="out")


# --------------------------------------------------------------------------- #
# A live (value)->reply reasoner caller for the in-memory env seam, which calls
# ``reasoners[name](value)`` with a single positional arg.
# --------------------------------------------------------------------------- #
def _live_reasoner_caller():
    from any_llm import acompletion

    async def caller(value: Any) -> Any:
        result = await complete_reasoner(
            get_reasoner(REASONER), value, acompletion=acompletion
        )
        return result.reply

    return caller


# --------------------------------------------------------------------------- #
# Shared driver: stream events for a 2-turn conversation, print state + verdict.
# --------------------------------------------------------------------------- #
async def _drive(handle, *, send_full_transcript: bool) -> None:
    """Run the scripted conversation against an open SessionHandle.

    ``send_full_transcript`` is for the CMA backend, whose handle does not thread
    a carrier across turns: the driver feeds the full running transcript as each
    message so the hosted model still sees turn 1 when answering turn 2.
    """
    agen = handle.events()
    replies: list[str] = []
    transcript: list[str] = []

    async def _drain_turn() -> None:
        # Per turn the backends emit: turn(started), emit(reply), turn(done).
        while True:
            event: SessionEvent = await asyncio.wait_for(agen.__anext__(), timeout=120)
            tag = (
                f"turn={event.turn}"
                if event.is_turn
                else f"seq={event.seq} payload={event.payload!r}"
                if event.is_emit
                else f"reason={event.reason!r} fatal={event.fatal}"
                if event.is_error
                else f"reason={event.reason!r}"
            )
            print(f"  [event] {event.kind:<7} {tag}")
            if event.is_emit:
                replies.append(str(event.payload))
            if event.is_error and event.fatal:
                raise RuntimeError(f"fatal session error: {event.reason}")
            if event.is_turn and event.turn == "done":
                return
            if event.is_closed:
                return

    for i, user_msg in enumerate(SCRIPT, start=1):
        transcript.append(f"user: {user_msg}")
        payload = (
            "\n".join(transcript) if send_full_transcript else user_msg
        )
        print(f"\n>>> turn {i} user: {user_msg}")
        await handle.send(payload)
        await _drain_turn()
        if replies:
            transcript.append(f"assistant: {replies[-1]}")

    print("\n--- final state ---")
    state = await handle.state()
    carrier = state.get("carrier")
    print(f"  carrier: {carrier!r}")
    print(f"  replies: {replies!r}")

    await handle.close("demo-done")
    # Drain remaining events through Closed so nothing is left unretrieved.
    try:
        while True:
            event = await asyncio.wait_for(agen.__anext__(), timeout=30)
            print(f"  [event] {event.kind:<7} reason={event.reason!r}")
            if event.is_closed:
                break
    except (StopAsyncIteration, asyncio.TimeoutError):
        pass

    last = replies[-1].upper() if replies else ""
    recall = CODEWORD in last
    print(f"\nSTATEFUL_RECALL={'yes' if recall else 'no'}")


# --------------------------------------------------------------------------- #
# Backends.
# --------------------------------------------------------------------------- #
async def run_local() -> None:
    from composable_agents.session import LocalSessionHandle

    print("=== backend: local (in-memory live session, REAL anthropic think) ===")
    session = build_session()
    handle = await LocalSessionHandle.open(
        session,
        reasoners={REASONER: _live_reasoner_caller()},
    )
    await _drive(handle, send_full_transcript=False)


async def run_temporal() -> None:
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Worker
    from temporalio.worker.workflow_sandbox import (
        SandboxedWorkflowRunner,
        SandboxRestrictions,
    )

    from composable_agents.execution.activities import WorkerContext, configure
    from composable_agents.execution.harness import SessionWorkflow  # noqa: F401
    from composable_agents.execution.llm import make_llm_caller
    from composable_agents.execution.session_store import InMemorySessionStore
    from composable_agents.execution.worker import ACTIVITIES, WORKFLOWS

    print("=== backend: temporal (durable SessionWorkflow + REAL LlmCaller) ===")
    print("    (using WorkflowEnvironment.start_time_skipping(); real Anthropic")
    print("     calls run inside the invokeReasoner activity)")

    env = await WorkflowEnvironment.start_time_skipping()
    try:
        task_queue = "ca-session-demo"
        # The worker's LLM seam is the REAL multi-provider any-llm caller.
        ctx = WorkerContext(
            session_store=InMemorySessionStore(empty_value=[]),
            llm=make_llm_caller(),
        )
        configure(ctx)
        worker = Worker(
            env.client,
            task_queue=task_queue,
            workflows=WORKFLOWS,
            activities=ACTIVITIES,
            workflow_runner=SandboxedWorkflowRunner(
                restrictions=SandboxRestrictions.default.with_passthrough_modules(
                    "composable_agents"
                )
            ),
        )
        async with worker:
            session = build_session()
            agent = Agent(MODEL, name="session_demo_temporal")
            handle = await agent.open(
                session=session,
                backend="temporal",
                client=env.client,
                session_id=f"session-demo-{uuid.uuid4()}",
                task_queue=task_queue,
            )
            await _drive(handle, send_full_transcript=False)
    finally:
        await env.shutdown()


async def run_cma() -> None:
    from composable_agents.execution.cma_anthropic import AnthropicCMAClient
    from composable_agents.execution.cma_session import CMASessionHandle

    print("=== backend: cma (Anthropic Claude Managed Agents beta, hosted model) ===")
    print("    NOTE: CMASessionHandle creates a fresh hosted session per turn and")
    print("    does NOT thread a carrier; the driver threads the full transcript")
    print("    in each message so recall still holds (caveat in the report).")

    model = "claude-haiku-4-5-20251001"  # bare slug for the CMA API
    client = AnthropicCMAClient(model=model, system=SYSTEM)
    handle = await CMASessionHandle.open(
        client=client,
        tools={},
        agent={"name": "session_demo_cma", "tools": []},
    )
    await _drive(handle, send_full_transcript=True)


BACKENDS = {
    "local": run_local,
    "temporal": run_temporal,
    "cma": run_cma,
}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in BACKENDS:
        print(f"usage: python examples/session_demo.py <{'|'.join(BACKENDS)}>")
        raise SystemExit(2)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set. Run: set -a; source .env; set +a")
        raise SystemExit(1)
    asyncio.run(BACKENDS[sys.argv[1]]())


if __name__ == "__main__":
    main()
