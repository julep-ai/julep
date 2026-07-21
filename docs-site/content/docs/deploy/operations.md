---
title: "Operations"
description: "Runbooks for operating workers and sessions in production, plus reaching the Temporal UI."
---

Operational runbooks for running julep in production. Each section is self-contained; the shared prerequisite is a deployed worker (see [Deploy on Temporal](/docs/deploy/temporal) or [Deploy on Kubernetes](/docs/deploy/kubernetes)).

## Operating workers

Workers are disposable Temporal pollers. Temporal workflow history is the
durable source of truth; projection, trace, pod logs, and KEDA metrics are
derived views. Roll back image/env/bundle/ledger pointers; do not edit workflow
history or treat projection as recovery state.

Related docs: [docs index](/docs), [concepts](/docs/concepts/model), [spec](/docs/internals/specification), [Temporal deploy](/docs/deploy/temporal), [Kubernetes deploy](/docs/deploy/kubernetes), [provider resilience](/docs/guides/providers-and-resilience), and [capabilities](/docs/guides/capabilities-and-safety).

#### When To Use

Use this when production Julep workers need deploy, scale, drain,
rollback, or wedged-flow triage. This is the Temporal/Kubernetes path:
`FlowWorkflow`, `AgentWorkflow`, `SessionWorkflow`, `julep worker`,
and KEDA's `temporal` scaler on task-queue backlog.

Do not use it for DBOS operations. DBOS runs through `julep.execution.dbos_backend`, rejects `race`/`hedge`/`quorum`, and uses DBOS queues/workflows instead of Temporal polling.

#### Prerequisites

Install the runtime extras your image needs:

```bash
python -m pip install --pre 'julep[temporal]'
python -m pip install --pre 'julep[providers,http,otel]'
python -m pip install --pre 'julep[store,wasm]'
```

You need Temporal address/namespace/task queue, Kubernetes rights for
Deployments/Secrets/HPAs/KEDA `ScaledObject`s, an image that runs
`julep worker`, provider/tool credentials as Secrets, and one
`WorkerContext` factory. Use `WORKER_CONTEXT_FACTORY=yourapp.worker:make_context`
for an app-specific image, or
`WORKER_CONTEXT_FACTORY=julep.execution.bundle_worker:make_context`
plus `STORE_URL`, `JULEP_BUNDLES`, and `JULEP_BUNDLE_ALLOWED_SIGNERS` for the generic
signed-bundle worker.

#### Procedure

1. Set operator variables.

   ```bash
   export JULEP_ENV=prod
   export AGENT=triage
   export NS=julep-prod
   export WORKER_DEPLOY=julep-worker
   export TASK_QUEUE=julep
   export TEMPORAL_ADDRESS=temporal-frontend.temporal.svc.cluster.local:7233
   export TEMPORAL_NAMESPACE=default
   export IMAGE=registry.example.com/julep-worker:2026-06-25
   export WORKER_CONTEXT_FACTORY=yourapp.worker:make_context
   export SMOKE_INPUT='"TICKET-42"'
   ```

2. Preflight source and publish the frozen artifact.

   ```bash
   julep doctor
   julep lint "$AGENT"
   julep deploy "$AGENT" --env "$JULEP_ENV"
   julep status "$AGENT" --env "$JULEP_ENV"
   ```

   Healthy result: discovery is `ok`, lint prints `clean`, deploy prints an
   agent plus `sha256:` artifact prefix, and status is `clean` with exit `0`.
   `julep status` exit `3` means drift or freeze error.

3. Create namespace and runtime Secret.

   ```bash
   kubectl create namespace "$NS" --dry-run=client -o yaml | kubectl apply -f -
   kubectl -n "$NS" create secret generic julep-worker-secrets \
     --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
     --dry-run=client -o yaml | kubectl apply -f -
   ```

   Healthy result: commands print `created` or `configured`. Secret keys must
   match what the `WorkerContext` factory reads.

4. Apply the worker Deployment.

   ```bash
   cat <<YAML | kubectl apply -f -
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: ${WORKER_DEPLOY}
     namespace: ${NS}
     labels: {app: ${WORKER_DEPLOY}}
   spec:
     replicas: 1
     selector:
       matchLabels: {app: ${WORKER_DEPLOY}}
     template:
       metadata:
         labels: {app: ${WORKER_DEPLOY}}
       spec:
         terminationGracePeriodSeconds: 45
         containers:
           - name: worker
             image: ${IMAGE}
             envFrom:
               - secretRef: {name: julep-worker-secrets}
             env:
               - {name: WORKER_CONTEXT_FACTORY, value: "${WORKER_CONTEXT_FACTORY}"}
               - {name: TEMPORAL_ADDRESS, value: "${TEMPORAL_ADDRESS}"}
               - {name: TEMPORAL_NAMESPACE, value: "${TEMPORAL_NAMESPACE}"}
               - {name: TEMPORAL_TASK_QUEUE, value: "${TASK_QUEUE}"}
               - {name: WORKER_GRACEFUL_SHUTDOWN_S, value: "30"}
               - {name: WORKER_HEALTH_PORT, value: "8080"}
             ports:
               - {containerPort: 8080, name: health}
             livenessProbe:
               httpGet: {path: /healthz, port: health}
               periodSeconds: 10
             readinessProbe:
               httpGet: {path: /readyz, port: health}
               periodSeconds: 5
   YAML
   ```

   Healthy result: Kubernetes accepts the manifest, and
   `terminationGracePeriodSeconds` is greater than `WORKER_GRACEFUL_SHUTDOWN_S`.
   For Temporal Cloud, also set `TEMPORAL_API_KEY` from a Secret and
   `TEMPORAL_TLS=true`.

5. Wait for rollout and probe the worker.

   ```bash
   kubectl rollout status deployment/"$WORKER_DEPLOY" -n "$NS" --timeout=180s
   kubectl get pods -n "$NS" -l app="$WORKER_DEPLOY"
   kubectl port-forward -n "$NS" deployment/"$WORKER_DEPLOY" 18080:8080
   curl -fsS http://127.0.0.1:18080/healthz
   curl -fsS http://127.0.0.1:18080/readyz
   ```

   Healthy result: rollout completes; `/healthz` prints `ok`; `/readyz` prints
   `ready`. During drain, readiness returns HTTP 503 while liveness continues to
   report the event loop.

6. Attach KEDA to Temporal backlog.

   ```bash
   cat <<YAML | kubectl apply -f -
   apiVersion: keda.sh/v1alpha1
   kind: ScaledObject
   metadata:
     name: ${WORKER_DEPLOY}-temporal
     namespace: ${NS}
   spec:
     scaleTargetRef:
       name: ${WORKER_DEPLOY}
     minReplicaCount: 0
     maxReplicaCount: 20
     pollingInterval: 5
     cooldownPeriod: 120
     triggers:
       - type: temporal
         metadata:
           endpoint: "${TEMPORAL_ADDRESS}"
           namespace: "${TEMPORAL_NAMESPACE}"
           taskQueue: "${TASK_QUEUE}"
           queueTypes: "workflow,activity"
           targetQueueSize: "5"
           activationTargetQueueSize: "0"
   YAML
   kubectl wait -n "$NS" --for=condition=Ready scaledobject/"${WORKER_DEPLOY}-temporal" --timeout=120s
   kubectl get hpa -n "$NS"
   ```

   Healthy result: `ScaledObject` is `Ready=True` and an HPA exists. If the HPA
   metric is `<unknown>`, check endpoint, namespace, queue, scaler auth, and
   Temporal backlog-stat support.

7. Smoke a deployed run and observe scale-from-backlog.

   ```bash
   kubectl get deployment "$WORKER_DEPLOY" -n "$NS" -w
   julep run "$AGENT" --env "$JULEP_ENV" --input "$SMOKE_INPUT"
   ```

   Healthy result: `julep run` prints `output: ...`; the Deployment scales up when
   backlog appears and scales down after `cooldownPeriod`. Temporal UI shows
   `FlowWorkflow`, `AgentWorkflow`, or `SessionWorkflow`.

8. Verify graceful drain during an upgrade.

   ```bash
   kubectl rollout restart deployment/"$WORKER_DEPLOY" -n "$NS"
   kubectl rollout status deployment/"$WORKER_DEPLOY" -n "$NS" --timeout=180s
   kubectl get pods -n "$NS" -l app="$WORKER_DEPLOY" -w
   ```

   Healthy result: old pods enter `Terminating`, readiness is removed before
   process exit, and new pods become ready. The entrypoint handles
   `SIGTERM`/`SIGINT` by stopping polling and letting in-flight activities finish
   within `WORKER_GRACEFUL_SHUTDOWN_S`; unfinished work is retried by Temporal.

#### Verification

Run after every deploy, scale change, and rollback:

```bash
julep status "$AGENT" --env "$JULEP_ENV"
julep run "$AGENT" --env "$JULEP_ENV" --input "$SMOKE_INPUT"
kubectl rollout status deployment/"$WORKER_DEPLOY" -n "$NS" --timeout=180s
kubectl get scaledobject "${WORKER_DEPLOY}-temporal" -n "$NS"
kubectl logs -n "$NS" deployment/"$WORKER_DEPLOY" --since=30m
```

Healthy result: `julep status` is `clean`; `julep run` returns expected output from
the deployed artifact; the worker has replicas when backlog exists; the
`ScaledObject` is ready; logs do not show repeated `PureDriftError`,
`CapabilityDenied`, `PlanRejected`, `ValidationError`, `FreezeError`,
`PrincipalRequired`, or `ResilienceExhausted`.

For a live flow, use Temporal UI or a `temporalio.client.Client` handle to query
`openGates` and `projection`. `openGates` should be empty unless waiting on
`human_gate(...)`; `projection` should show planned/did/failed events,
`costByShape`, and `pending`.

#### Rollback

Bad image or worker env:

```bash
kubectl rollout history deployment/"$WORKER_DEPLOY" -n "$NS"
kubectl rollout undo deployment/"$WORKER_DEPLOY" -n "$NS"
kubectl rollout status deployment/"$WORKER_DEPLOY" -n "$NS" --timeout=180s
```

Bad signed-bundle pointer:

```bash
kubectl set env deployment/"$WORKER_DEPLOY" -n "$NS" \
  JULEP_BUNDLES="$PREVIOUS_JULEP_BUNDLES" \
  JULEP_BUNDLE_ALLOWED_SIGNERS="$PREVIOUS_JULEP_BUNDLE_ALLOWED_SIGNERS"
kubectl rollout status deployment/"$WORKER_DEPLOY" -n "$NS" --timeout=180s
```

Healthy result: startup bundle verification and `verifyPures` pass. Missing
`STORE_URL`, unknown signer, or tampered bundle fails closed before the worker
accepts workflow tasks.

Bad deployed artifact: restore the previous `.julep/deploys/${JULEP_ENV}.json` record
from the release artifact or source-control history. Do not re-freeze current
source as rollback. Then run:

```bash
julep status "$AGENT" --env "$JULEP_ENV"
julep run "$AGENT" --env "$JULEP_ENV" --input "$SMOKE_INPUT"
```

Bad scale setting:

```bash
kubectl patch scaledobject "${WORKER_DEPLOY}-temporal" -n "$NS" --type=merge \
  -p '{"spec":{"minReplicaCount":1,"maxReplicaCount":4}}'
kubectl wait -n "$NS" --for=condition=Ready scaledobject/"${WORKER_DEPLOY}-temporal" --timeout=120s
```

#### Escalation

Start with the failing seam.

- Workflow running, no progress: inspect Temporal UI for `RUN_ID`, workflow
  type, task queue, current event, last activity failure, retry state, child
  workflow state, and whether it is parked on `submitHuman`. Query `openGates`;
  non-empty means it is waiting for human input.
- Pods healthy, tasks do not start:

  ```bash
  kubectl describe scaledobject "${WORKER_DEPLOY}-temporal" -n "$NS"
  kubectl get hpa -n "$NS"
  kubectl describe deployment "$WORKER_DEPLOY" -n "$NS"
  kubectl logs -n "$NS" deployment/"$WORKER_DEPLOY" --since=30m
  ```

  Escalate endpoint/auth/HPA issues to the platform owner.
- Non-retryable policy failure: `CapabilityDenied`, `PlanRejected`,
  `ValidationError`, `FreezeError`, `PureDriftError`, and `PrincipalRequired`
  are settled decisions. Capture diagnostics, artifact hash, capability
  manifest, `pinned_pures`, image digest, and bundle refs.
- Provider failure: if using `make_resilient_llm_caller`, capture each
  `AttemptRecord` (`model`, `provider`, `outcome`, `detail`). `CONFIG` means bad
  key/model/request and must not be masked by fallback.
- Missing projection/trajectory: capture workflow history first. Projection,
  `PostgresProjection`, OTel, Langfuse, and trajectory sinks are derived or
  best-effort; they are not durability.

Before escalating, attach `RUN_ID`, workflow type, task queue, Temporal
namespace, `julep status` output, deploy ledger entry, worker image digest, worker
env excluding secrets, KEDA YAML, HPA status, worker logs, and `openGates` /
`projection` query output if available.

## Operating sessions

Use this runbook when a long-lived session is already deployed, or about to be deployed, and you need to keep sending messages, stream `SessionEvent`s, drain it cleanly, resume a durable consumer, or recover a stuck session. For authoring rules and the user-facing model, read [Sessions](/docs/guides/sessions) first.

Sessions are root `Op.LOOP` artifacts guarded by `recv(...)`. The production durable path is Temporal `SessionWorkflow`; local sessions are in-memory; CMA opens one hosted Anthropic managed-agent session per turn and does not thread the framework carrier between turns.

#### Prerequisites

- Python `>=3.12`.
- For Temporal production: `pip install --pre 'julep[temporal,providers]'`
  or the source-checkout equivalent:

```bash
pip install -e '.[temporal,providers]'
```

- For CMA: install the CMA extra and set Anthropic credentials:

```bash
pip install -e '.[cma,providers]'
export ANTHROPIC_API_KEY=...
```

- Temporal access: frontend address, namespace, task queue, and credentials.
  `julep worker` reads `TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`,
  `TEMPORAL_TASK_QUEUE`, `TEMPORAL_API_KEY`, and `TEMPORAL_TLS`.
- Worker context: `WORKER_CONTEXT_FACTORY=module:attr` must resolve to a
  callable returning `julep.execution.effects.WorkerContext`.
- Production storage: if you run multi-replica workers or enable
  `history_threshold`, use shared implementations for `WorkerContext.session_store`
  and `WorkerContext.blob_store`. `InMemorySessionStore` is only process-local.
- Operator access: worker logs, Temporal Web/Cloud for the workflow id, and the
  ability to run `julep doctor` in the application checkout.

#### Known-good smoke

1. Load provider credentials and run the backend smoke you are about to operate.

```bash
set -a; source .env; set +a
uv run --extra dev --extra providers python examples/session_demo.py local
uv run --extra dev --extra providers python examples/session_demo.py temporal
uv run --extra dev --extra providers --extra cma python examples/session_demo.py cma
```

Healthy result: each selected backend prints `turn=started`, one or more `emit`
events, `turn=done`, then `STATEFUL_RECALL=yes`. The demo exits early with
`ANTHROPIC_API_KEY not set. Run: set -a; source .env; set +a` when the key is
missing. Run the CMA command only when the CMA beta is enabled for the key.

#### Procedure

1. Start a Temporal worker for the session lane.

```bash
export WORKER_CONTEXT_FACTORY=yourapp.worker:make_context
export TEMPORAL_ADDRESS=localhost:7233
export TEMPORAL_NAMESPACE=default
export TEMPORAL_TASK_QUEUE=julep
export WORKER_HEALTH_PORT=8080
julep worker
```

Healthy result: the process remains running and the readiness probe below
returns `200`. The worker registers `FlowWorkflow`, `SessionWorkflow`,
`AgentWorkflow`, and the activities from
`julep.execution.worker.WORKFLOWS` and `ACTIVITIES`.

2. Check readiness before accepting traffic.

```bash
curl -fsS http://127.0.0.1:8080/readyz
```

Healthy result: `ready`. During drain, this endpoint returns `503` with
`not ready`; `/healthz` should still return `ok` while the event loop is alive.

3. Open the chosen backend.

```python
# Local: dev and smoke only.
handle = await agent.open(session=chat, backend="local", channel_capacity=100)
```

```python
# Temporal: production.
from temporalio.client import Client

client = await Client.connect("localhost:7233", namespace="default")
handle = await agent.open(
    session=chat, backend="temporal", client=client,
    session_id="support-session-123", task_queue="julep",
    history_threshold=10000, channel_capacity=100,
)
```

```python
# CMA: hosted per-turn session; resend transcript if you need memory.
from julep.execution.cma_anthropic import AnthropicCMAClient

cma_client = AnthropicCMAClient(
    model="claude-haiku-4-5-20251001",
    system="You are a concise assistant.",
)
handle = await agent.open(session=chat, backend="cma", client=cma_client)
```

Healthy result: `agent.open(...)` returns a `SessionHandle`. Temporal rejects the
open if `client=` is missing, if the root artifact is not `Op.LOOP`, or if the
session capability manifest cannot be admitted.

4. Start exactly one event consumer per handle.

```python
agen = handle.events()
```

Healthy result: no event is yielded until the session receives input. Calling
`handle.events()` a second time on the same handle raises `JulepError`
with `single-consumer` in the message.

5. Send one message with an idempotency key.

```python
ack = await handle.send(
    {"text": "hello"},
    idempotency_key="support-session-123:turn-1",
)
print(ack)
```

Healthy result:

```python
{"seq": 1, "channel": "in"}
```

Reusing the same `idempotency_key` with the same payload returns the original
ack. Reusing it with a different payload is rejected.

6. Drain the turn from the streaming surface.

```python
while True:
    event = await agen.__anext__()
    print(event.kind, event.channel, event.seq, event.turn, event.reason, event.payload)
    if event.is_error and event.fatal:
        raise RuntimeError(event.reason)
    if event.is_closed or (event.is_turn and event.turn == "done"):
        break
```

Healthy result for one successful turn: `turn started`, one or more `emit`
records on the output channel, then `turn done`. The full event stream ends only
on `Closed`, not at a turn boundary.

7. Monitor the keep-messaging loop.

```python
state = await handle.state()
parked = await handle.open_receives()
print(state)
print(parked)
```

Healthy Temporal/local idle state: `closed` is `False`, `pending` is empty or
bounded, and `open_receives()` contains a record like `{"channel": "in", "seq": 2}`.
For CMA, `open_receives()` returns `[]`; `state()` reports `pending`, `turns`,
`capacity`, and `closed`.

8. Drain safely before a deploy, scale-in, or handoff.

Stop producers first. Keep the event consumer running until every accepted
message has reached `turn done`. Then close:

```python
await handle.close("operator-drain")
while True:
    event = await agen.__anext__()
    print(event.kind, event.reason)
    if event.is_closed:
        break
```

Healthy result: local and Temporal flush an in-flight turn before `Closed`.
Temporal `close()` waits for quiescence and raises `TimeoutError("session close
did not quiesce")` if the workflow does not append the durable closed event
within its client-side deadline.

9. Resume a durable Temporal session after a consumer crash.

```python
from julep.execution.harness import TemporalSessionHandle
from temporalio.client import Client

client = await Client.connect("localhost:7233", namespace="default")
wf = client.get_workflow_handle("support-session-123")
handle = TemporalSessionHandle(wf, in_channel="in", out_channel="out")
agen = handle.events()
```

Healthy result: the new handle reads the workflow's unacked durable event log.
Downstream consumers should de-dupe emitted payloads by `(channel, seq)`, because
a crash after delivery but before the lazy `ack_events` update can replay the
last delivered event.

10. Resume local or CMA only by reopening.

Local has no durable reattach path; process exit loses the handle and carrier.
CMA also has no framework carrier; reopen a handle and resend the transcript or
other application state in the next message if memory is required.

#### Verification

Run `julep doctor` in the app checkout:

```bash
julep doctor
```

Healthy result includes `[ok ] discovery: ...` and `[ok ] temporal: temporalio
installed`. `langfuse` may warn when `LANGFUSE_HOST` is intentionally unset.

Query the Temporal workflow directly when the public handle is unavailable:

```python
from temporalio.client import Client

client = await Client.connect("localhost:7233", namespace="default")
wf = client.get_workflow_handle("support-session-123")
print(await wf.query("state"))
print(await wf.query("open_receives"))
print(await wf.query("events"))
```

Healthy result: `state["closed"]` is `False`, `open_receives` shows the next
parked channel when idle, and `events` is empty or contains only unacked durable
records. Verify output pressure clears by continuing to pull `handle.events()`;
Temporal evicts emitted output buffers through the event ack path.

#### Rollback

Rollback is not an in-place mutation of a live `SessionWorkflow`.

1. Stop new producers for the affected `session_id`.
2. Drain accepted messages through `turn done`, then call
   `await handle.close("rollback")`.
3. Start a replacement session with a new `session_id` on the last known good
   worker image, task queue, and session definition.
4. Replay only application-level messages that were not acknowledged by
   `handle.send(...)`. Use stable `idempotency_key` values for replay.

If the workflow is wedged and cannot close, preserve it for forensics and route
traffic to the replacement `session_id`. Terminate the old workflow only through
your Temporal operator process after capturing the data listed below.

#### Recovery

- `ChannelFull` on `send`: stop producers, start or resume the event consumer,
  and drain emits. `channel_capacity` is set when the session is opened; increase
  it only on a new session.
- `open_receives()` shows `in`: the loop is healthy and waiting for input. Send
  the next message or close the session.
- `pending` grows while no worker logs show `SessionWorkflow` progress: the
  worker is not polling the task queue, is not ready, or is pointed at the wrong
  namespace/task queue. Check `TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`,
  `TEMPORAL_TASK_QUEUE`, and `/readyz`.
- No `open_receives()` and no emits: the turn is inside the body. Check worker
  logs and Temporal history for activity retries, `PureDriftError`,
  `CapabilityDenied`, provider failures, or a tool call that never returns.
- `Error(fatal=False)`: the turn failed with recoverable `SessionTurnError`; the
  carrier is unchanged for that turn and the session can accept the next message.
- `Error(fatal=True)` followed by `Closed`: the session is terminal. Open a new
  session after fixing the cause.
- `recv(..., timeout_s=...)` timeout on Temporal: the workflow re-enters `recv`
  and exposes the channel in `open_receives()` again. A receive timeout alone is
  not a terminal failure.

#### Escalation packet

Before escalating, capture:

- `session_id`, backend, task queue, namespace, worker image/version, and
  whether the handle was local, Temporal, or CMA.
- The last successful `send` ack and the idempotency key used.
- `await handle.state()` and `await handle.open_receives()`, or the equivalent
  raw Temporal `state`, `open_receives`, and `events` query output.
- Worker logs covering the stuck turn, plus the Temporal workflow history or
  Temporal Web link for `SessionWorkflow`.
- Any projection or trajectory sink records configured on `WorkerContext`; if
  the session was driven through `julep`, include `julep trace <run-id>` output.
- `julep doctor` output from the same checkout and environment.
- For CMA, the Anthropic model slug, whether `environment` was a string id,
  dict, or omitted, and whether the driver resent the transcript.

Do not escalate with only "the session hung". The minimum useful state is:
`state`, `open_receives`, the last event seen from `events()`, the last `send`
ack, and the worker/Temporal logs for that same `session_id`.

## Reaching the Temporal UI

The Temporal web UI runs on the EKS demo cluster but is never exposed to the public
internet. Access is gated by three layers:

1. **Internal ALB** — the `temporal-web` service sits behind an internal-scheme ALB
   (no public IP), reachable only from inside the VPC.
2. **SSM bastion** — the only network path into the VPC. A tiny EC2 instance with no
   inbound rules and scoped egress, reachable only through AWS Systems Manager.
3. **AWS IAM** — you must be able to assume the shared `temporal-team` role and hold
   `ssm:StartSession` on the bastion. That same role is the EKS access-entry principal,
   so assuming it also grants cluster-admin `kubectl`.

```
laptop (IAM creds)
  │  assume temporal-team  →  aws ssm start-session (port forward)
  ▼
SSM bastion (no public ingress, egress: 443→SSM, 80+53→VPC only)
  │  localhost:8233  →  <internal-ALB>:80
  ▼
internal ALB (EKS Auto Mode, scheme=internal)
  ▼
temporal-web:8080
```

#### One-time setup (operator)

Set the team's IAM principals and apply:

```hcl
# infra/terraform/envs/demo/terraform.tfvars
team_principal_arns = ["arn:aws:iam::<account-id>:user/alice", ...]
```

```bash
scripts/eks-demo-up.sh
```

This creates the `<name_prefix>-team` role, the SSM bastion, the internal ALB, and the
EKS access entry. The ALB Ingress is applied by the script (not Terraform) because EKS
Auto Mode configures ALB scheme/subnets through the `IngressClassParams` CRD.

#### Opening the UI (team member)

```bash
ASSUME_TEAM_ROLE=1 scripts/temporal-ui.sh
# wait for "Waiting for connections...", then open:
open http://localhost:8233
```

Override the local port with `LOCAL_PORT=9233 scripts/temporal-ui.sh`. If you already
run as the team role (or have mapped your own principal), drop `ASSUME_TEAM_ROLE=1`.

Prerequisites on the laptop: the AWS CLI, the
[Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html),
and `kubectl`.

#### Security model

- The Temporal UI has **no application-level auth**. Every gate is infrastructure: the
  ALB is internal, the only path in is the SSM bastion, and the bastion is IAM-gated.
- The bastion's egress is restricted to `443→SSM`, `80→VPC` (the ALB), and `53→VPC`
  (DNS). It deliberately **cannot** reach RDS (`5432`) or anything else, so the
  port-forward document can't be repurposed to tunnel to other VPC resources.
- `ssm:StartSession` is scoped to this bastion and the port-forward document, with
  `ssm:SessionDocumentAccessCheck` enforced.

To also pin the tunnel *destination* (so it can only ever reach the Temporal ALB), add
a Route53 private record for the ALB and a custom SSM document with the host/port fixed,
then scope `StartSession` to that document. Left out of the baseline because the team is
already cluster-admin and the egress scoping covers the main risk.

<!-- ported-by julep-docs-site: deploy/operations -->
