"""WORKER_CONTEXT_FACTORY module for the k3d episode-summary flow demo.

Runs inside the pod (``WORKER_CONTEXT_FACTORY=flow_worker:make_context``).
Imports the example as a flat module (the Dockerfile copies both
``episode_summary_flow.py`` and this file into ``/app``), serves the example's
native hands as an in-pod HTTP microservice on localhost, and wires the real
any-llm caller — same pattern as tooling/k3d-llm-demo/llm_weather_agent.py.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import episode_summary_flow

HAND_PORT = 8799

TOOLS = episode_summary_flow.TOOLS


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
        capabilities=episode_summary_flow.build().capabilities,
    )
