# Capabilities and Safety

Composable Agents treats authority as data. A flow is not allowed to discover a
tool at runtime, infer a model from a planner reply, or inherit a child agent's
hands. The compile pipeline freezes the IR, validates it, applies the capability
manifest, checks approval dominance, and admits races before the artifact can run
in strict mode. See [README.md](../README.md), [concepts.md](concepts.md), and
[SPEC §5](SPEC.md#5-compile-pipeline).

## Deny-by-default

Grant sections distinguish absence from emptiness:

- absent section / `None` -> unconstrained;
- present-but-empty / `[]` -> deny all;
- present with entries -> explicit allow-list.

This is normative in [SPEC §7.1](SPEC.md#71-absent-vs-empty). In
`CapabilityManifest`, section-presence flags preserve the distinction for
`tools`, `brains`, `models`, `subflows`, `memory`, `network`, and `mcp_servers`.
If `tools` is present, every `call(...)` and every inline `app(tools=[...])`
tool must be named in that list. A hallucinated or ungranted tool is denied with
`CAP_TOOL_DENIED` or `CAP_APP_TOOL_DENIED`, not routed to an ambient executor.

The same stance applies at run time where the manifest has run-time seams:
`network` gates native HTTP hand egress, `budget` gates estimated spend, and
`maxCalls` is exposed to the Temporal environment as deterministic workflow
state.

## The capability manifest

The manifest is a YAML/dict mapping parsed by `CapabilityManifest.from_yaml(...)`
or `CapabilityManifest.from_dict(...)`. Its grant sections are:

- `tools`: tool refs by key; native hands use `name`, MCP tools use
  `server/tool`. A grant may include `effect`, `idempotency`, `approval`, and
  `maxCalls`.
- `brains`: named brain refs.
- `models`: resolved `Brain.model` ids.
- `subflows`: invokable child-flow refs.
- `memory`: `ContextScope` values such as `local`, `summary`, and
  `whole_session`.
- `network`: native hand egress domains.
- `mcp_servers` / `mcpServers`: server -> optional version constraint.
- `budget`: `cost`, `tokens`, and `wallSeconds` / `wall_seconds`.

```yaml
tools:
  - name: search/web
    effect: read
    idempotency: native
    maxCalls: 8
  - name: send_email
    effect: dangerous
    idempotency: required
    approval: required
brains:
  - support-controller
models:
  - claude-sonnet-4-6
network:
  - hands.internal.example
mcp_servers:
  search: ">=1"
budget:
  cost: 0.25
  tokens: 20000
  wallSeconds: 60
```

`CapabilityManifest.to_json()` emits the frozen manifest shape used in the
deployment artifact. See [SPEC §7.2](SPEC.md#72-grant-sections).

## Contract assertions

MCP annotations are hints, not authority. The framework reads `readOnlyHint`,
`idempotentHint`, `destructiveHint`, and `openWorldHint`, but defaults
conservatively to `effect=write` and `idempotency=none` unless a tool is
asserted in the capability manifest. A `ToolGrant` asserts a contract only when
both `effect` and `idempotency` are present.

Race-family combinators make that distinction blocking. `race(...)`,
`hedge(...)`, and `quorum(...)` cancel losers, so every branch must be read-only
or native/required-idempotent, and the contract must be asserted. Unasserted
branches fail with `RACE_UNASSERTED`; unsafe asserted contracts fail with
`RACE_UNSAFE`; sub-agents inside a race fail with `RACE_SUB`. See
[SPEC §5](SPEC.md#5-compile-pipeline) and [SPEC §8.3](SPEC.md#83-race--hedge--quorum).

## Attenuation

A sub-agent runs with its own authority. The parent does not inherit the child's
tools, and the child does not get to exceed the parent's visible grant surface.
This is why `Agent` capabilities are represented as subflows rather than merged
tool lists:

```python
triage = Agent(brain="haiku", tools=[search, classify], name="triage.v1")
desk = Agent(brain="claude-sonnet-4-6", tools=[lookup, triage])
```

`desk` may call `lookup` and may invoke `triage.v1` as a sub-capability. It does
not gain direct access to `search` or `classify`. Plain `Flow` capabilities used
inside an `Agent` are stricter: they may only call tools already granted to the
agent, otherwise construction raises `CAP_APP_FLOW_UNGRANTED_TOOL`. Capability
name collisions fail with `CAP_APP_TOOL_COLLISION`; unnamed flow capabilities
fail with `CAP_APP_FLOW_UNNAMED`.

## Approval gates

`human_gate(prompt=..., timeout_s=...)` lowers to a reserved native hand,
`__human_gate__`. The Temporal harness turns that leaf into a durable
`submitHuman` signal wait; timeout returns:

```json
{"approved": false, "reason": "timeout", "input": "<original input>"}
```

A tool whose frozen contract has `effect=dangerous`, or whose grant sets
`approval: required`, must be dominated by a preceding `human_gate(...)`.
Strict deploy rejects an ungated path with `APPROVAL_UNGATED`. Inline agent
tools are more constrained: `app(...)` / `Agent(...)` cannot directly call an
approval-required or dangerous tool, because a controller loop is not itself an
approval gate; this is `CAP_APP_APPROVAL_TOOL`.

Approval gating is specified in [SPEC §7.3](SPEC.md#73-approval-gating-new--required),
human gate behavior in [SPEC §8.6](SPEC.md#86-human-gate), and agent-loop grant
behavior in [SPEC §10](SPEC.md#10-agent-loop).

## Dev vs prod enforcement

`EnforcementMode` has two values: `STRICT` and `DEV`. `deploy(..., mode="strict")`
and `Agent(..., mode="strict")` are production disposition. Blocking diagnostics
raise `ValidationError` when `strict=True`, the default.

Dev mode is an iteration aid:

```python
deployment = deploy(flow, snapshot, capabilities=caps, mode="dev")
print(deployment.prod_gap_summary())
for diag in deployment.prod_gap:
    print(diag.code, diag.message)
```

`deploy(..., mode="dev")` and `Agent(..., mode="dev")` return the deployment and
retain would-block diagnostics in `deployment.prod_gap`. `prod_gap_summary()`
groups them into deploy-facing buckets such as ungranted tool, ungranted
brain/model, ungated dangerous/approval call, and version pin mismatch.

Temporal runs stay prod-strict. `Deployment.run(...)` refuses a dev-mode
deployment and requires the prod gap to be resolved before running on Temporal.
Use dev mode locally, then rebuild with `mode="strict"` or `mode="prod"` before
starting a durable run.

## Teaching diagnostics

Diagnostics are plain data:

```python
Diagnostic(
    code: str,
    node_id: str,
    message: str,
    severity: str = "error",
    hint: str | None = None,
    help_url: str | None = None,
    source: SourceSpan | None = None,
)
```

`explain(diagnostics)` renders blocking diagnostics before warnings. It prints
`fix:` from the diagnostic's `hint` or from the built-in `HINTS` table. Source
capture is opt-in with `COMPOSABLE_AGENTS_SOURCE_CAPTURE=1` or
`set_source_capture(True)`; when enabled, freeze maps authored source spans onto
normalized node ids and `explain(...)` includes `--> file:line`.

```text
Blocking diagnostics:
- [CAP_TOOL_DENIED@$] error: tool 'srv/denied' is not granted
    --> app.py:42  (call(mcp("srv", "denied")))
    fix: Add this tool to the capability manifest's tools: allow-list, or remove the call.
```

Codes with built-in remediation text include `APPROVAL_UNGATED`,
`CAP_TOOL_DENIED`, `CAP_APP_TOOL_DENIED`, `CAP_APP_APPROVAL_TOOL`,
`UNKNOWN_PURE`, `CAP_VERSION_PIN`, `CAP_MODEL_DENIED`,
`CAP_MODEL_ID_DENIED`, `CAP_SUBFLOW_DENIED`, `CAP_APP_SUBFLOW_DENIED`,
`CAP_SERVER_DENIED`, and `CAP_MEMORY_DENIED`.

Related: [getting-started.md](getting-started.md), [deploy-temporal.md](deploy-temporal.md),
[examples.md](examples.md), [design/typed-flow.md](design/typed-flow.md), and
[CONTRIBUTING.md](../CONTRIBUTING.md).
