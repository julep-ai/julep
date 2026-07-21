# Julep

Julep — durable, composable AI agents. Flows that crash and resume, retry safely, and explain every step.

Julep builds agents as **composable, durable dataflows** instead of ad-hoc loops: flows can crash and resume, retry safely, explain every step through a derived projection, and deny any tool the model was not explicitly allowed to call. The primary authoring surface is define-by-construction `@flow`: ordinary Python names graph steps while registered tools, pures, reasoners, branches, fan-out, retries, and timeouts compile to the same frozen wire-format IR. The pure core stays dependency-free, while the Temporal layer is optional.

---

## Install

```bash
pip install --pre julep
```

Julep 3 currently ships as a release candidate, so the `--pre` flag is required; it drops once `3.0.0` is final.

---

## Quickstart

10 minutes, no API key. Install the base package and run this as a normal Python script:

```python
from typing import TypedDict

from julep import Reasoner, deploy, flow, pure, think, tool


class SupportReply(TypedDict):
    reply: str


@tool(effect="read", idempotent=True)
def lookup_ticket(ticket: str) -> dict[str, str]:
    return {
        "ticket": ticket,
        "queue": "billing",
        "summary": "Use the duplicate-charge runbook.",
    }


@pure("ticket_prompt")
def ticket_prompt(hit: dict[str, str]) -> dict[str, str]:
    return {"queue": hit["queue"], "context": hit["summary"]}


support_reply = Reasoner(
    name="support_reply",
    model="anthropic:claude-haiku-4-5-20251001",
    system="Draft one concise support reply as JSON.",
    reply=SupportReply,
)


@flow
def triage(ticket: str) -> dict[str, str]:
    hit = lookup_ticket(ticket, retries=2, timeout_s=5)
    prompt = ticket_prompt(hit)
    answer = think(support_reply, prompt, timeout_s=10)
    return hit | answer


def fake_support_reply(value: dict[str, str]) -> SupportReply:
    return {"reply": f"{value['queue']}: {value['context']}"}


deployment = deploy(triage, tools=[lookup_ticket], reasoners=[support_reply])
result = deployment.dry_run(
    "Customer was charged twice.",
    reasoners={"support_reply": fake_support_reply},
)

print(result.value)
```

`@flow` runs once at definition time with data handles. Registered tools, registered pures, `think(...)`, `cond(...)`, `switch(...)`, `each(...)`, and `reschedule(...)` append graph steps instead of doing runtime work; `|` merges records and `h["key"]` plucks fields. `deploy(..., tools=..., reasoners=...)` freezes the tool and reasoner surface, and `dry_run(...)` executes locally with in-memory tools and deterministic fake reasoners. See the larger `@flow` examples in `examples/episode_summary_flow.py` and `examples/cluster_labeling_flow.py`.

Use `mcp_tool(server, tool)` inside `@flow` for an MCP reference. Its schemas
and behavior contract come from the frozen MCP snapshot; handle-valued keyword
arguments build its input record directly. `examples/episode_summary_flow.py`
shows snapshot-backed MCP reads and writes with a local `mcp_call` fake.

---

## The CLI

`julep` is the developer CLI for a whole **module of agents** — "dbt for agents, terminal-native." Point it at a directory; it discovers every `@flow`/`Agent(...)`, treats each as a node in a cross-agent graph, and gives you one selection grammar across every verb:

```bash
julep ls                                  # list agents (name · kind · tags)
julep show triage                         # one agent's kind, source location, tags, calls
julep graph                               # the cross-agent DAG as Graphviz DOT
julep run triage --input '"TICKET-42"'    # execute locally, stream the trace tree
julep lint +triage                        # validate an agent and everything it depends on
julep test triage                         # run pytest for the selected agents
julep trace <run-id>                      # render a cached run's trace tree + Langfuse link
julep doctor                              # preflight: discovery, git, Langfuse, Temporal
julep deploy triage --env staging         # freeze → publish → record in the deploy ledger
julep serve api --migrate                 # run the self-hosted FastAPI control plane
```

Selectors compose: `tag:support`, `state:modified` (Slim-CI), `+agent`/`agent+`/`@agent` graph traversal, `a,b` intersection, `--exclude`. Full reference: **[docs-site/content/docs/guides/using-the-cli.md](docs-site/content/docs/guides/using-the-cli.md)**.

For production applications, declare an explicit object instead of adding a
second discovery convention:

```python
from collections.abc import Mapping

from julep import Application, CapabilityManifest, McpSnapshot, PipelineSpec


def load_live_memory_tools_snapshot(
    environment: Mapping[str, str],
) -> McpSnapshot:
    # Use the selected deployment environment to call tools/list.
    ...

application = Application("memory", [
    PipelineSpec(
        name="episode_summary",
        flow=summary_flow,
        reasoners=(summary_reasoner,),
        capabilities=CapabilityManifest.from_file("summary-capabilities.yaml"),
        lane="summary",
        eval_packages=("prompts/episode_summary.ctx",),
        snapshot=memory_tools_snapshot,
        snapshot_source=load_live_memory_tools_snapshot,
    ),
])
```

For `julep plan`, `apply`, and application-level `status`, each
`snapshot_source` receives a read-only mapping made from the selected
environment's `[vars]` followed by `[worker_environment]` (worker values win on
duplicate names). Secret-backed worker variables are intentionally absent:
`worker_secret_environment` contains Kubernetes Secret references, not values,
and those values exist only in the worker at runtime. The callback must return
an `McpSnapshot`; pass any credential needed for schema discovery through a
non-secret control-plane mechanism rather than expecting a Secret value here.

Point `[tool.julep].application` at that object with a `module:attribute` value.
Each deployable environment also names the worker's explicit context factory;
ordinary and Secret-backed worker environment can be reconciled with the lane:

```toml
[tool.julep.env.staging]
temporal_address = "temporal-frontend.temporal.svc.cluster.local:7233"
release_store = "s3://julep-releases/julep"
worker_image = "registry.example/memory@sha256:<digest>"
worker_context_factory = "memory.worker:build_context"
worker_service_account = "julep-worker"
worker_priority_class = "julep-model-worker"
payload_encryption_secret = "temporal-payload-codec"

[tool.julep.env.staging.worker_environment]
MEMORY_TOOLS_MCP_URL = "http://memory-tools/mcp-internal"
JULEP_BUNDLE_ALLOWED_SIGNERS = "<64-hex-ed25519-public-key>"

[tool.julep.env.staging.worker_secret_environment.MEMORY_TOOLS_JWT_PRIVATE_KEY]
secret_name = "memory-tools-jwt"
key = "private-key"
```

`payload_encryption_secret` is required for application releases and names an
existing Kubernetes Secret in `kubernetes_namespace` with `keyring` and
`active-key-id` entries. The PriorityClass is optional: set
`worker_priority_class` only when shared cluster infrastructure provisions it
(the EKS demo does); omit it on ordinary clusters.

`julep plan --env staging` reports artifact, MCP-schema, Helm/KEDA, and runtime
drift; `julep apply --env staging` publishes an immutable S3-CAS release and
reconciles one digest-pinned Helm release per lane and immutable release on a
release-specific task queue, without changing traffic;
`julep status --env staging` aggregates the release and live lane state. That
application-level status path is selected only when `[tool.julep].application` is
configured and no selector or `--exclude` is supplied; selected status queries
continue to inspect the legacy per-agent deploy ledger.

Application publishing requires a 64-hex Ed25519 seed (or a file containing
one) in `JULEP_BUNDLE_SIGNING_KEY`. In production, set the corresponding 64-hex
public key in the non-secret `JULEP_BUNDLE_ALLOWED_SIGNERS` worker environment;
`apply` rejects a configured allow-list that does not contain the publishing
key. Read-only `plan` and application-level `status` need that public allow-list
(or the private key as a local fallback). Install `julep[store,temporal]` for
S3 publication and Temporal workers, plus any pipeline-specific extras. The
control-plane host also needs authenticated `helm`, `kubectl`, and `temporal`
CLIs; `apply --publish-only` skips Helm reconciliation.

`julep worker` runs continuously from its environment contract. A positive
`--smoke-test-seconds N` verifies Temporal connectivity, polls the configured
queue for `N` seconds, drains, and exits; the default `0` keeps serving.

---

## Extras

The base install is authoring + compile only (PyYAML). Optional extras add runtime surfaces:

| Extra | `pip install --pre 'julep[...]'` | Adds |
|---|---|---|
| `temporal` | `julep[temporal]` | durable execution on Temporal (workflows, activities, worker, client helpers) |
| `dbos` | `julep[dbos]` | durable execution on DBOS / Postgres (steps, flow workflow, chaining runner) |
| `http` | `julep[http]` | native HTTP tool calls from the `callTool` activity |
| `cma` | `julep[cma]` | httpx transport for the CMA HTTP adapter |
| `mcp` | `julep[mcp]` | official MCP SDK, httpx, PyJWT, and cryptography for MCP references, snapshots, calls, and auth |
| `server` | `julep[server]` | FastAPI/Uvicorn control plane, SSE, Postgres store, Temporal gateway, cryptography, and httpx |
| `dotctx` | `julep[dotctx]` | rich `.ctx` layout (Jinja2 templates compiled into registered renderers) |
| `yglu` | `julep[yglu]` | Yglu-evaluated `settings.yaml` (mem-mcp `.ctx` compatibility) |
| `providers` | `julep[providers]` | multi-provider `LlmCaller` via any-llm (pair with provider extras) |
| `otel` | `julep[otel]` | OpenTelemetry span export of the projection |
| `langfuse` | `julep[langfuse]` | Langfuse OTLP/HTTP export of the projection |
| `store` | `julep[store]` | artifact distribution stores + bundle signing primitives |
| `wasm` | `julep[wasm]` | sandboxed wasm execution of bundle-sourced pures (wasmtime host) |

`julep.HAVE_TEMPORAL` reports whether the runtime is available; the package imports and compiles flows either way.

---

## Looking for Julep v1?

Julep v1 (the agents API platform) is preserved on the [`v1` branch](https://github.com/julep-ai/julep/tree/v1) and its docs at v1.docs.julep.ai. Julep 3 is a ground-up rewrite; there is no migration path — v1 and v3 are different products.

---

## License

This project is licensed under Apache-2.0. See [LICENSE](LICENSE).
