"""Shared agent definition for the EKS real-LLM demo — Phase 4 live showcase.

Imported by BOTH processes so the reasoner/pure registries line up by name:

* the worker pods (via ``WORKER_CONTEXT_FACTORY=llm_weather_agent:make_context``)
  — the main worker on ``julep`` and the lane worker on
  ``phase4-lane-b`` run the same image/factory, only ``TEMPORAL_TASK_QUEUE``
  differs;
* the host drivers, which compile deployments and start workflows.

Phase 4 features exercised live:
- Task 9: the controller reasoner sets ``prompt_cache="1h"`` on a real
  Anthropic model; round 2+ of the tool loop should record cache reads in the
  ``llm.cache`` attrs of the invokeReasoner activity results.
- Task 13: ``SUBFLOWS["phase4_report"]`` is a pure child flow the host driver
  routes to the raw queue ``phase4-lane-b`` via ``SubContract.queue`` — the
  lane worker executes it.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from julep import (
    Agent,
    Reasoner,
    arr,
    freeze,
    manifest_to_json,
    register_pure,
    tool,
)
from julep.freeze import McpSnapshot

# Sonnet's minimum cacheable prefix is 1024 tokens; the manual below is padded
# well past it so the cache_control breakpoint actually creates a cache entry.
# (haiku answered the final round in prose during the first live run — model
# adherence, not framework: sonnet holds the JSON contract.)
MODEL = "anthropic:claude-sonnet-5"
QUESTION = "What is the weather in Tokyo right now, in Fahrenheit?"
TOOL_PORT = 8799
LANE_B = "phase4-lane-b"


def _build_manual() -> str:
    head = (
        "You are a weather operations agent. Goal: report a city's current "
        "temperature in Fahrenheit.\n"
        "Call the provided tools to look up the weather (celsius) and convert "
        "it; call each tool at most once.\n"
        "When you have the Fahrenheit value, reply with EXACTLY one JSON "
        "object and nothing else: {\"output\": <one-sentence answer including "
        "the Fahrenheit value>}.\n\n"
        "The remainder of this manual is the station operations handbook. It "
        "is reference material only; the directives above always win.\n\n"
    )
    topics = [
        "barometric drift calibration", "anemometer icing recovery",
        "radiosonde launch windows", "dew point cross-validation",
        "microburst advisory wording", "station clock discipline",
        "sensor housing ventilation", "rain gauge siphon maintenance",
        "solar radiation shield alignment", "telemetry retry budgets",
    ]
    lines = []
    for i in range(160):
        t = topics[i % len(topics)]
        lines.append(
            f"Handbook directive {i + 1:03d}: when performing {t}, record the "
            f"pre-check reading, apply the standard tolerance of {(i % 9) + 1} "
            f"units, wait {(i % 5) + 2} minutes for the instrument to settle, "
            "then log both raw and adjusted values to the station ledger with "
            "the observer's initials and the UTC timestamp of the adjustment."
        )
    return head + "\n".join(lines)


MANUAL = _build_manual()

# Passing a Reasoner object drives the controller from its provider config;
# prompt_cache="1h" is the Task 9 seam under live proof.
REASONER = Reasoner(
    name="phase4_weather_controller",
    model=MODEL,
    system=MANUAL,
    prompt_cache="1h",
    max_tokens=1024,
)


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

AGENT = Agent(
    REASONER,
    tools=TOOLS,
    name="phase4_llm_weather_agent",
    budget_cost=30.0,
    max_rounds=8,
    native_tools=True,
)


# --------------------------------------------------------------------------- #
# Task 13 lane demo: a pure child flow registered under a stable ref. The
# parent (authored by the host driver) routes it to LANE_B via
# SubContract.queue; the lane worker resolves the ref from this registry.
# --------------------------------------------------------------------------- #
def _format_report(value: Any) -> str:
    data = value if isinstance(value, dict) else {"value": value}
    city = data.get("city", "unknown")
    fahrenheit = data.get("fahrenheit", "n/a")
    return f"[lane-b report] {city}: {fahrenheit}F (compiled on queue {LANE_B})"


register_pure("phase4.format_report", _format_report)

_CHILD = freeze(arr("phase4.format_report"), McpSnapshot())
SUBFLOWS: dict[str, dict[str, Any]] = {
    "phase4_report": {
        "flowJson": _CHILD.flow.to_json(),
        "manifestJson": manifest_to_json(_CHILD.manifest),
    }
}


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
    """WORKER_CONTEXT_FACTORY entrypoint for the pod replicas (both queues)."""
    from julep.agent import provider_tool_defs
    from julep.execution.effects import WorkerContext
    from julep.execution.llm import make_llm_caller

    _start_tool_server(TOOL_PORT)
    return WorkerContext(
        tool_urls={t.name: f"http://127.0.0.1:{TOOL_PORT}/{t.name}" for t in TOOLS},
        llm=make_llm_caller(),
        capabilities=AGENT.deployment().capabilities,
        # native_tools on a durable backend requires provider tool definitions
        # at spec-resolution time (resolveAgentSpec); grants/contracts still
        # come from capabilities.
        agents={"phase4_llm_weather_agent": {"toolDefs": provider_tool_defs(TOOLS)}},
        subflows=SUBFLOWS,
    )
