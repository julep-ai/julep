"""Shared agent definition for the k3d real-LLM demo.

Imported by BOTH processes so the brain registry lines up by name:

* the worker pod (via ``WORKER_CONTEXT_FACTORY=llm_weather_agent:make_context``),
  where ``invokeBrain`` resolves the brain from this process's registry and the
  any-llm caller makes the real Anthropic calls;
* the host driver (``drive_llm.py``), which only compiles the deployment and
  starts the AgentWorkflow on the task queue.

The @tool hands are served as an in-pod HTTP microservice on localhost, per the
framework's native-hands model (same wiring as examples/temporal_durable_agent.py,
containerized).
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from composable_agents import Agent, tool

MODEL = "anthropic:claude-haiku-4-5-20251001"
QUESTION = "What is the weather in Tokyo right now, in Fahrenheit?"
HAND_PORT = 8799


def _arg(payload: Any, key: str) -> Any:
    """Tolerate provider habits: bare argument or a one-key named object."""
    if isinstance(payload, dict):
        if key in payload:
            return payload[key]
        return next(iter(payload.values()), payload)
    return payload


@tool(effect="read", idempotent=True)
def get_weather(payload: Any) -> dict[str, Any]:
    """Get the current weather for a city (celsius + conditions)."""
    city = _arg(payload, "city")
    table = {
        "Tokyo": {"celsius": 22, "conditions": "partly cloudy"},
        "Paris": {"celsius": 18, "conditions": "sunny"},
    }
    return table.get(city, {"celsius": 20, "conditions": "clear"})


@tool(effect="read", idempotent=True)
def to_fahrenheit(payload: Any) -> float:
    """Convert a Celsius temperature to Fahrenheit."""
    return float(_arg(payload, "celsius")) * 9 / 5 + 32


TOOLS = [get_weather, to_fahrenheit]

INSTRUCTIONS = (
    "You are a weather agent. Goal: report a city's current temperature "
    "in Fahrenheit.\n"
    "Each turn you receive a JSON object with two keys:\n"
    "  - 'input': the result of your last action (initially the user's "
    "question).\n"
    "  - 'trace': the tools you have already called this run, in order.\n"
    "Reply with EXACTLY one JSON object and nothing else:\n"
    "  - {\"tool\": <name>, \"input\": <arg>} to call a tool, or\n"
    "  - {\"output\": <one-sentence answer including the Fahrenheit "
    "value>} when finished.\n"
    "Procedure (do each step once; never call a tool already shown in "
    "'trace'):\n"
    "  1. trace empty -> call get_weather with the city name, e.g. "
    "{\"tool\": \"get_weather\", \"input\": \"Tokyo\"}.\n"
    "  2. trace has get_weather but not to_fahrenheit -> 'input' now holds "
    "{\"celsius\": n, ...}; call {\"tool\": \"to_fahrenheit\", \"input\": "
    "n}.\n"
    "  3. trace has to_fahrenheit -> 'input' is the Fahrenheit number; "
    "reply with {\"output\": \"...\"}."
)

# Module-level so a bare import registers the brain under a stable name in
# whichever process imports this (worker pod or host driver).
AGENT = Agent(
    MODEL,
    tools=TOOLS,
    name="k3d_llm_weather_agent",
    instructions=INSTRUCTIONS,
    budget_cost=30.0,
    max_rounds=8,
)


# --------------------------------------------------------------------------- #
# In-pod hand server: POST {"input": v} -> JSON result (callHand contract).
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

    def log_message(self, *args: Any) -> None:  # silence probe noise
        return


def _start_hand_server(port: int) -> ThreadingHTTPServer:
    _HandHandler.tools_by_name = {t.name: t for t in TOOLS}
    srv = ThreadingHTTPServer(("127.0.0.1", port), _HandHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def make_context() -> Any:
    """WORKER_CONTEXT_FACTORY entrypoint for the pod replica."""
    from composable_agents.execution.effects import WorkerContext
    from composable_agents.execution.llm import make_llm_caller

    _start_hand_server(HAND_PORT)
    return WorkerContext(
        hand_urls={t.name: f"http://127.0.0.1:{HAND_PORT}/{t.name}" for t in TOOLS},
        llm=make_llm_caller(),
        capabilities=AGENT.deployment().capabilities,
    )
