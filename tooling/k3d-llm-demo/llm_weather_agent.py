"""Shared agent definition for the k3d real-LLM demo.

Imported by BOTH processes so the reasoner registry lines up by name:

* the worker pod (via ``WORKER_CONTEXT_FACTORY=llm_weather_agent:make_context``),
  where ``invokeReasoner`` resolves the reasoner from this process's registry and the
  any-llm caller makes the real Anthropic calls;
* the host driver (``drive_llm.py``), which only compiles the deployment and
  starts the AgentWorkflow on the task queue.

The @tool tools are served as an in-pod HTTP microservice on localhost, per the
framework's native-tools model (same wiring as examples/temporal_durable_agent.py,
containerized).
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from composable_agents import Agent, tool

MODEL = "openai:gpt-5.4-mini"
QUESTION = "What is the weather in Tokyo right now, in Fahrenheit?"
TOOL_PORT = 8799


# Multi-param signatures on purpose: they derive a real object input_schema
# (properties + required), which native tool-calling providers require for
# function.parameters — and which lets the model actually fill in arguments.
@tool(effect="read", idempotent=True)
def get_weather(city: str, units: str = "celsius") -> dict[str, Any]:
    """Get the current weather for a city (celsius + conditions)."""
    del units
    table = {
        "Tokyo": {"celsius": 22, "conditions": "partly cloudy"},
        "Paris": {"celsius": 18, "conditions": "sunny"},
    }
    return table.get(city, {"celsius": 20, "conditions": "clear"})


@tool(effect="read", idempotent=True)
def to_fahrenheit(celsius: float, ndigits: int = 1) -> float:
    """Convert a Celsius temperature to Fahrenheit."""
    return round(float(celsius) * 9 / 5 + 32, ndigits)


TOOLS = [get_weather, to_fahrenheit]

INSTRUCTIONS = (
    "You are a weather agent. Goal: report a city's current temperature "
    "in Fahrenheit.\n"
    "Call the provided tools to look up the weather (celsius) and convert "
    "it; call each tool at most once.\n"
    "When you have the Fahrenheit value, reply with EXACTLY one JSON "
    "object and nothing else: {\"output\": <one-sentence answer including "
    "the Fahrenheit value>}."
)

# Module-level so a bare import registers the reasoner under a stable name in
# whichever process imports this (worker pod or host driver).
# native_tools=True: phase-3 native provider tool-calling — the model emits
# provider tool_calls (not the JSON controller protocol), the loop executes
# them effect-fenced, and the transcript replays in provider grammar.
AGENT = Agent(
    MODEL,
    tools=TOOLS,
    name="k3d_llm_weather_agent",
    instructions=INSTRUCTIONS,
    budget_cost=30.0,
    max_rounds=8,
    native_tools=True,
)


# --------------------------------------------------------------------------- #
# In-pod tool server: POST {"input": v} -> JSON result (callTool contract).
# --------------------------------------------------------------------------- #
class _ToolHandler(BaseHTTPRequestHandler):
    tools_by_name: dict[str, Any] = {}

    def do_POST(self) -> None:  # noqa: N802
        name = self.path.strip("/")
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        tool_obj = self.tools_by_name[name]
        result = tool_obj.bound_tool(payload["input"])
        body = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:  # silence probe noise
        return


def _start_tool_server(port: int) -> ThreadingHTTPServer:
    _ToolHandler.tools_by_name = {t.name: t for t in TOOLS}
    srv = ThreadingHTTPServer(("127.0.0.1", port), _ToolHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def make_context() -> Any:
    """WORKER_CONTEXT_FACTORY entrypoint for the pod replica."""
    from composable_agents.agent import provider_tool_defs
    from composable_agents.execution.effects import WorkerContext
    from composable_agents.execution.llm import make_llm_caller

    _start_tool_server(TOOL_PORT)
    return WorkerContext(
        tool_urls={t.name: f"http://127.0.0.1:{TOOL_PORT}/{t.name}" for t in TOOLS},
        llm=make_llm_caller(),
        capabilities=AGENT.deployment().capabilities,
        # native_tools on a durable backend requires provider tool definitions
        # at spec-resolution time (resolveAgentSpec); grants/contracts still
        # come from capabilities.
        agents={"k3d_llm_weather_agent": {"toolDefs": provider_tool_defs(TOOLS)}},
    )
