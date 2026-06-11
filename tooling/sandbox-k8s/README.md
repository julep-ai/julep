# sandbox-k8s — k3s + KEDA in a Claude Code sandbox VM

Run the [deploy-kubernetes.md](../../docs/deploy-kubernetes.md) stack — k3s,
KEDA's `temporal` scaler, a Temporal dev server, and the `composable-agents
worker` container — inside a Claude Code sandbox VM, for live testing of the
autoscaling path. Verified 2026-06: a 12-workflow burst scales the worker
Deployment 0 → 4 (ready in ~10s), all flows complete, and the cooldown returns
it to 0.

```bash
sudo bash tooling/sandbox-k8s/setup.sh
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
python3 tooling/sandbox-k8s/drive.py 12   # burst; watch `kubectl get deploy ca-worker -w`
```

**Sandbox-only.** The setup edits `/etc/docker/daemon.json` and assumes a
disposable root VM. Do not run it on a real machine — there, the docs guide
applies as written, with none of these workarounds.

## Why each workaround exists

The sandbox kernel is locked down in ways that break Kubernetes in specific,
diagnosable places:

| Symptom | Cause | Workaround |
|---|---|---|
| Every pod sandbox fails with `runc create failed: can't get final child's PID from pipe: EOF` | The kernel forbids lowering `oom_score_adj`; kubelet/cri-dockerd hardcode `-998` for pause containers | `runc-noadj`, a runc wrapper that clamps negative `process.oomScoreAdj` in the OCI bundle to 0, installed as docker's `default-runtime` |
| k3d / kind nodes never run any pod | `/sys/fs/cgroup` is a bare tmpfs — no cgroup controllers exist to delegate into nested nodes | Skip docker-in-docker entirely: run `k3s server --docker` on the host so pods are plain docker containers |
| `pip install` inside `docker build` fails with `SSL: CERTIFICATE_VERIFY_FAILED` | Sandbox egress goes through a TLS-intercepting proxy; the image doesn't trust its CA | `Dockerfile` copies the host CA bundle and sets `PIP_CERT`/`SSL_CERT_FILE` |
| Registry pulls inside a k3d node fail with `x509: certificate signed by unknown authority` | Same proxy CA, now for containerd inside the node | Moot once on `k3s --docker` (host dockerd already trusts it) |
| Restarting dockerd loses locally built images | The image moves between image stores across the restart | `setup.sh` configures dockerd before building anything |

Other one-time landmines: `pkill -f "k3s server"` matches the invoking shell's
own command line (use `k3s serve[r]`), and pods reach the host at the flannel
gateway `10.42.0.1` (k3s default), which is what `worker.yaml` and the
ScaledObject use for `TEMPORAL_ADDRESS` / `endpoint`.

## Files

- `setup.sh` — the whole sequence: docker runtime wrapper, binaries (direct
  release downloads), Temporal dev server, k3s, KEDA, image build, deploy.
- `runc-noadj` — the OCI wrapper. The only file with any life outside the
  demo: any kubelet-on-this-sandbox use case needs it.
- `Dockerfile` / `demo_worker.py` — worker image from the local checkout plus
  a `WORKER_CONTEXT_FACTORY` whose MCP caller sleeps 1s, so bursts produce a
  visible backlog.
- `worker.yaml` — Deployment + KEDA ScaledObject, the docs example adapted to
  this sandbox (gateway endpoint, `imagePullPolicy: Never`, small windows:
  `pollingInterval: 5`, `cooldownPeriod: 30`, `targetQueueSize: 2`).
- `drive.py` — freezes `call(mcp("srv", "inc"))`, starts N workflows on the
  queue, asserts the results.
