---
title: "Deploy on Kubernetes"
description: "Containerized workers, SIGTERM drain, health probes, and KEDA autoscaling on task-queue backlog."
---

Workers are stateless: Temporal owns all run state, so a worker replica is
interchangeable and disposable. That makes the scaling story plain Kubernetes —
a Deployment of worker pods, autoscaled by [Temporal](/docs/deploy/temporal).

## The container entrypoint

```bash
julep worker
```

reads its configuration from the environment:

| Variable | Default | Meaning |
|---|---|---|
| `WORKER_CONTEXT_FACTORY` | **required** | `module:attr` of a zero-arg callable (sync or async) returning the `WorkerContext` |
| `TEMPORAL_ADDRESS` | `localhost:7233` | Temporal frontend `host:port` |
| `TEMPORAL_NAMESPACE` | `default` | Temporal namespace |
| `TEMPORAL_TASK_QUEUE` | `julep` | task queue this replica polls (one queue per lane) |
| `TEMPORAL_API_KEY` | unset | Temporal Cloud API key; setting it defaults TLS on |
| `TEMPORAL_TLS` | true iff API key set | force TLS on/off |
| `WORKER_GRACEFUL_SHUTDOWN_S` | `30` | drain window for in-flight activities after SIGTERM |
| `WORKER_MAX_CONCURRENT_ACTIVITIES` | SDK default | per-replica activity slots |
| `WORKER_MAX_CONCURRENT_WORKFLOW_TASKS` | SDK default | per-replica workflow-task slots |
| `WORKER_HEALTH_PORT` | off | HTTP port serving `GET /healthz` and `GET /readyz` |

`WORKER_CONTEXT_FACTORY` is required and has no default: a `WorkerContext`
holds live callables (the MCP caller, the LLM, registries), which cannot come
from env vars, and a worker silently running without them would be a degraded
mode, not a deployment. Ship a factory in your image:

```python
# yourapp/worker.py
from julep.execution.effects import WorkerContext

def make_context() -> WorkerContext:  # async def also works
    return WorkerContext(
        mcp_call=your_mcp_caller,
        llm=your_resilient_llm,        # see provider-resilience.md
        capabilities=load_capabilities(),
        subflows=load_subflow_registry(),
    )
```

and set `WORKER_CONTEXT_FACTORY=yourapp.worker:make_context`. Flags override
the environment for local runs: `julep worker --task-queue
lane-embeddings --address localhost:7233`.

Lifecycle per replica: the probe listener starts first (liveness is green while
the pod connects), the worker polls, readiness flips to 200. On SIGTERM,
readiness flips to 503, polling stops, in-flight activities get
`WORKER_GRACEFUL_SHUTDOWN_S` to finish, and the process exits 0. Anything not
finished in the window is retried elsewhere by Temporal — nothing is lost, so
KEDA scale-in is safe by construction. A worker crash exits non-zero and the
pod restarts.

## Image

```dockerfile
FROM python:3.12-slim
RUN pip install --no-cache-dir --pre 'julep[temporal]'
COPY yourapp /app/yourapp
ENV PYTHONPATH=/app \
    WORKER_CONTEXT_FACTORY=yourapp.worker:make_context \
    WORKER_HEALTH_PORT=8080
ENTRYPOINT ["julep", "worker"]
```

## Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: julep-worker
spec:
  replicas: 1                      # KEDA takes over below
  selector:
    matchLabels: {app: julep-worker}
  template:
    metadata:
      labels: {app: julep-worker}
    spec:
      # Must exceed WORKER_GRACEFUL_SHUTDOWN_S so the drain finishes
      # before the kubelet sends SIGKILL.
      terminationGracePeriodSeconds: 45
      containers:
        - name: worker
          image: yourrepo/julep-worker:latest
          env:
            - name: TEMPORAL_ADDRESS
              value: temporal-frontend.temporal.svc:7233
            - name: TEMPORAL_TASK_QUEUE
              value: julep
            - name: WORKER_GRACEFUL_SHUTDOWN_S
              value: "30"
          ports:
            - containerPort: 8080
              name: health
          livenessProbe:
            httpGet: {path: /healthz, port: health}
            periodSeconds: 10
          readinessProbe:
            httpGet: {path: /readyz, port: health}
            periodSeconds: 5
```

Workers take no inbound traffic (they poll Temporal), so the probes exist for
orchestration only: liveness restarts a wedged event loop, readiness reports
polling vs. draining.

## KEDA ScaledObject

KEDA's `temporal` scaler reads the task-queue backlog straight from the
Temporal frontend — no metrics pipeline required:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: julep-worker
spec:
  scaleTargetRef:
    name: julep-worker
  minReplicaCount: 0          # scale-to-zero; use >= 1 for a warm floor
  maxReplicaCount: 20
  cooldownPeriod: 120         # seconds idle before scaling back to zero
  triggers:
    - type: temporal
      metadata:
        endpoint: temporal-frontend.temporal.svc:7233
        namespace: default
        taskQueue: julep
        queueTypes: "workflow,activity"   # default is workflow only
        targetQueueSize: "5"              # backlog per replica
        activationTargetQueueSize: "0"    # any backlog wakes a 0-replica lane
```

Sizing notes:

- `targetQueueSize` is the backlog each replica is expected to absorb; pair it
  with `WORKER_MAX_CONCURRENT_ACTIVITIES` so a replica's slot count matches
  what KEDA assumes it can chew through.
- Scale-to-zero (`minReplicaCount: 0`) fits background lanes (embeddings,
  summaries, maintenance): the first dispatch queues in Temporal, KEDA sees the
  backlog, and a pod cold-starts within its polling interval. Latency-sensitive
  lanes keep `minReplicaCount: 1+` as a warm floor.
- One task queue per lane, one Deployment + ScaledObject per queue. Lanes scale
  independently and a backlog in one cannot starve another — the same intent as
  per-lane worker containers in a compose file, with the autoscaler attached.

## Temporal Cloud

Point both the worker and the scaler at Temporal Cloud with an API key:

```yaml
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: temporal-cloud-auth
spec:
  secretTargetRef:
    - parameter: apiKey
      name: temporal-cloud        # Secret with key `api-key`
      key: api-key
```

```yaml
  triggers:
    - type: temporal
      metadata:
        endpoint: <ns>.<account>.tmprl.cloud:7233
        namespace: <ns>.<account>
        taskQueue: julep
      authenticationRef:
        name: temporal-cloud-auth
```

For the worker, mount the same Secret as `TEMPORAL_API_KEY` (TLS turns on
automatically) and set `TEMPORAL_ADDRESS` / `TEMPORAL_NAMESPACE` to the cloud
endpoint and namespace.

## Multi-replica caveats

Replicas share nothing by default; three seams need shared backends once
replica count exceeds one:

- **Provider circuit breakers are per-process**
  ([Providers And Resilience](/docs/guides/providers-and-resilience)): each replica discovers a
  failing provider independently before its breaker opens. Acceptable at small
  counts; at larger ones the deterministic fallback chain is what bounds the
  damage.
- **`SessionStore` and `BlobStore`** must be shared services (Postgres, object
  store), not in-memory instances, or sessions and claim-checked payloads are
  visible only to the replica that wrote them.
- **Registry drift is caught, not prevented**: `verifyPures` compares
  deploy-pinned pure hashes against the replica's registry before effects run,
  so a stale image fails loudly. Roll images atomically per lane to avoid the
  noise.

Related: [Temporal](/docs/deploy/temporal),
[the Dispatch Boundary](/docs/concepts/dispatch-boundary),
[Providers And Resilience](/docs/guides/providers-and-resilience), [docs index](/docs).

<!-- ported-by julep-docs-site: deploy/kubernetes -->
