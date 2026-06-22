"""Push one synthetic run to a real Langfuse via OTLP, then verify ingestion.

De-risks the Langfuse integration: confirms the exact OTLP attribute keys, that
a nested span tree renders, that a generation shows tokens + derived cost, and
that stable derived IDs (trace=hash(run_id), span=hash(cid)) survive ingestion
so the trace can be fetched back by its known id (the Task 6 idempotency design).

Env: LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY.
Run: python spikes/langfuse_otlp/spike.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.id_generator import IdGenerator
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

HOST = os.environ["LANGFUSE_HOST"].rstrip("/")
PK = os.environ["LANGFUSE_PUBLIC_KEY"]
SK = os.environ["LANGFUSE_SECRET_KEY"]
AUTH = base64.b64encode(f"{PK}:{SK}".encode()).decode()

RUN_ID = f"spike-run-{int(time.time())}"
ROOT_CID = "__run_root__:" + RUN_ID
GEN_CID = "c0-reasoner"


def _trace_id(run_id: str) -> int:
    h = hashlib.sha256(("trace:" + run_id).encode()).digest()
    return int.from_bytes(h[:16], "big") or 1


def _span_id(cid: str) -> int:
    h = hashlib.sha256(("span:" + cid).encode()).digest()
    return int.from_bytes(h[:8], "big") or 1


class StableIdGenerator(IdGenerator):
    """Deterministic ids per (run_id, current cid). cid is set before each span."""

    def __init__(self, run_id: str) -> None:
        self._run_id = run_id
        self.current_cid = ROOT_CID

    def generate_trace_id(self) -> int:
        return _trace_id(self._run_id)

    def generate_span_id(self) -> int:
        return _span_id(self.current_cid)


idgen = StableIdGenerator(RUN_ID)
exporter = OTLPSpanExporter(
    endpoint=f"{HOST}/api/public/otel/v1/traces",
    headers={"Authorization": f"Basic {AUTH}", "x-langfuse-ingestion-version": "4"},
)
provider = TracerProvider(id_generator=idgen)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)
tr = trace.get_tracer("spike")

now = time.time_ns()
idgen.current_cid = ROOT_CID
root = tr.start_span("spike-run", start_time=now)
root.set_attribute("langfuse.trace.name", "spike-run")
root.set_attribute("langfuse.session.id", RUN_ID)
root_ctx = trace.set_span_in_context(root)

idgen.current_cid = GEN_CID
gen = tr.start_span("reasoner-call", start_time=now, context=root_ctx)
gen.set_attribute("langfuse.observation.type", "generation")
gen.set_attribute("gen_ai.request.model", "claude-opus-4-8")
gen.set_attribute("gen_ai.response.model", "claude-opus-4-8")
gen.set_attribute("gen_ai.usage.input_tokens", 1200)
gen.set_attribute("gen_ai.usage.output_tokens", 340)
gen.set_attribute("langfuse.observation.input", json.dumps({"q": "hello?"}))
gen.set_attribute("langfuse.observation.output", json.dumps({"a": "hi there"}))
gen.end(end_time=now + 2_000_000_000)
root.end(end_time=now + 2_500_000_000)

provider.shutdown()  # force flush

trace_hex = format(_trace_id(RUN_ID), "032x")
print(f"flushed. run_id={RUN_ID} trace_hex={trace_hex}")

# --- verify ingestion via the Langfuse public API (async on their side) -------
url = f"{HOST}/api/public/traces/{trace_hex}"
deadline = time.time() + 45
attempt = 0
while time.time() < deadline:
    attempt += 1
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {AUTH}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        obs = data.get("observations", [])
        gens = [o for o in obs if o.get("type") == "GENERATION"]
        print(f"[attempt {attempt}] trace found: name={data.get('name')!r} "
              f"observations={len(obs)} generations={len(gens)}")
        if gens:
            g = gens[0]
            usage = g.get("usage") or g.get("usageDetails") or {}
            cost = g.get("calculatedTotalCost") or g.get("totalCost") or g.get("costDetails")
            print("  generation:",
                  json.dumps({"model": g.get("model"),
                              "usage": usage,
                              "cost": cost,
                              "input_present": g.get("input") is not None,
                              "output_present": g.get("output") is not None}, default=str))
            print("RESULT: OK — trace + generation ingested.")
            sys.exit(0)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"[attempt {attempt}] HTTP {e.code}: {e.read().decode()[:200]}")
    except Exception as e:  # noqa: BLE001
        print(f"[attempt {attempt}] {type(e).__name__}: {e}")
    time.sleep(5)

print("RESULT: trace not confirmed within 45s (ingestion lag or auth/endpoint issue).")
sys.exit(1)
