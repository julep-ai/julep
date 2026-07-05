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
```

Selectors compose: `tag:support`, `state:modified` (Slim-CI), `+agent`/`agent+`/`@agent` graph traversal, `a,b` intersection, `--exclude`. Full reference: **[docs-site/content/docs/guides/using-the-cli.md](docs-site/content/docs/guides/using-the-cli.md)**.

---

## Extras

The base install is authoring + compile only (PyYAML). Optional extras add runtime surfaces:

| Extra | `pip install --pre 'julep[...]'` | Adds |
|---|---|---|
| `temporal` | `julep[temporal]` | durable execution on Temporal (workflows, activities, worker, client helpers) |
| `dbos` | `julep[dbos]` | durable execution on DBOS / Postgres (steps, flow workflow, chaining runner) |
| `http` | `julep[http]` | native HTTP tool calls from the `callTool` activity |
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
