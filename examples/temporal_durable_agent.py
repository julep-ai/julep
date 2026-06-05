"""Run a facade ``Agent``'s loop *durably* on a real Temporal server.

This is the end-to-end durable path (not the in-memory interpreter): the agent's
think -> call -> observe loop runs inside Temporal's ``AgentWorkflow``, each round
recorded in workflow history and replayable. The agent's ``@tool`` hands are
served over HTTP (the framework's "native hands as stateless HTTP microservices"
model); the controller brain is a deterministic in-process stub (no API key).

Prereqs (one-time, in another terminal):

    temporal server start-dev          # gRPC :7233, web UI http://localhost:8233

Then:

    .venv/bin/python examples/temporal_durable_agent.py

Watch it in the UI: http://localhost:8233 — open the latest workflow to see the
AgentWorkflow history (invokeBrain / callHand activities, each loop round).
"""

from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from temporalio.client import Client

from composable_agents import Agent, tool
from composable_agents.execution.activities import WorkerContext
from composable_agents.execution.worker import DEFAULT_TASK_QUEUE, build_worker

HAND_PORT = 8799
TEMPORAL_HOST = "localhost:7233"
UI = "http://localhost:8233"


# --------------------------------------------------------------------------- #
# Native @tool hands (read-only, idempotent). Each is served over HTTP below.
# --------------------------------------------------------------------------- #
@tool(effect="read", idempotent=True)
def lookup_account(account_id: str) -> dict[str, Any]:
    """Pretend account lookup."""
    return {
        "account_id": account_id,
        "plan": "pro",
        "status": "past_due",
        "balance_cents": 4200,
    }


@tool(effect="read", idempotent=True)
def classify_risk(account: dict[str, Any]) -> dict[str, Any]:
    """Classify churn/credit risk from an account record."""
    high = account.get("status") == "past_due" and account.get("balance_cents", 0) > 1000
    return {
        "account_id": account.get("account_id"),
        "risk": "high" if high else "low",
        "balance_cents": account.get("balance_cents"),
    }


TOOLS = [lookup_account, classify_risk]


# --------------------------------------------------------------------------- #
# Deterministic controller (the "brain"). Worker signature: (Brain, value).
# value == {"input": state.last, "trace": [...]}. Reply is the closed agent
# vocabulary; omitting "input" threads state.last into the call.
# --------------------------------------------------------------------------- #
async def scripted_controller(brain: Any, value: dict[str, Any]) -> dict[str, Any]:
    step = len(value.get("trace", []))
    if step == 0:
        return {"tool": "lookup_account"}      # input -> state.last (the account id)
    if step == 1:
        return {"tool": "classify_risk"}       # input -> state.last (the account record)
    return {"output": value["input"]}          # state.last (the risk classification)


# --------------------------------------------------------------------------- #
# A tiny stdlib HTTP hand server: POST {"input": v} -> JSON result, per the
# callHand native contract (Idempotency-Key header is accepted, not required).
# --------------------------------------------------------------------------- #
class _HandHandler(BaseHTTPRequestHandler):
    tools_by_name: dict[str, Any] = {}

    def do_POST(self) -> None:  # noqa: N802
        name = self.path.strip("/")
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        tool_obj = self.tools_by_name[name]
        result = tool_obj.bound_hand(payload["input"])
        body = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:  # silence
        return


def start_hand_server(tools: list[Any], port: int) -> ThreadingHTTPServer:
    _HandHandler.tools_by_name = {t.name: t for t in tools}
    srv = ThreadingHTTPServer(("127.0.0.1", port), _HandHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


async def main() -> None:
    hand_srv = start_hand_server(TOOLS, HAND_PORT)
    try:
        # The facade agent (tool-only -> deploys cleanly; registers its brain).
        agent = Agent(brain="triage-controller", tools=TOOLS, name="triage_agent", max_rounds=6)

        client = await Client.connect(TEMPORAL_HOST)
        ctx = WorkerContext(
            hand_urls={t.name: f"http://127.0.0.1:{HAND_PORT}/{t.name}" for t in TOOLS},
            llm=scripted_controller,
            capabilities=agent.deployment().capabilities,  # resolveAgentSpec grants from here
        )
        worker = build_worker(client, ctx, task_queue=DEFAULT_TASK_QUEUE)

        print(f"Deploying agent to Temporal ({TEMPORAL_HOST}); watch {UI}")
        async with worker:
            result = await agent.deploy(
                client, session_id="triage-run-1", input="acct-42"
            )

        print("\n=== durable run result ===")
        print("status:", result["status"], "| spent:", result.get("cost"))
        print("output:", json.dumps(result["output"]))
        print("trace:")
        for entry in result["trace"]:
            print(f"  - {entry['decision']} {entry.get('ref','')} (${entry['cost']})")
        print(f"\nInspect the workflow history in the UI: {UI}")
    finally:
        hand_srv.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
