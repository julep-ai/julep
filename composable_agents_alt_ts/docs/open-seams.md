# Open seams

## Freeze timing

Default in this scaffold: deploy-time freeze. The type-level option leaves room for run-time freeze later, but the implemented path freezes before deploy/start. Deploy-time freeze produces stable manifests and replay artifacts. Run-time freeze should be treated as a separate reproducibility mode if added.

## MCP session affinity

The `McpRuntime` interface receives `(cid, sessionId, tool, input)`. A host implementation can choose:

- session-per-call: simplest, worse latency
- worker-tier session pool keyed by `(server, sessionId)`: better for stateful MCP servers
- external MCP proxy service: best isolation and easiest horizontal scaling

## Continue-as-new

The workflow uses `workflowInfo().continueAsNewSuggested` inside the `app` loop. For long bounded critique loops, add a similar policy if loop bodies become large enough to threaten Temporal history limits.

## Projection path

The scaffold writes projection events from activities. The workflow interceptor hook is present but intentionally thin. Production can graduate to a Temporal history-export tailer if you want projection emission fully decoupled from application code.

## Model-judged routing

Do not put model calls directly in `alt`. Compile model judgments as `think -> alt(namedPure)` where the pure predicate reads the model output deterministically.
