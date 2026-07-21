# Generic runtime image

This directory is the single source of truth for the generic code-as-data worker
image used by the demos.

## What this image is

- A flow-agnostic `julep worker` runtime.
- Built once at framework cadence, then reused for every flow.
- Contains the installed framework with `temporal`, `store`, and `wasm` extras.
- Contains `uv` for the opt-in native dependency tier.

## What this image is not

- It is not a per-flow image.
- It does not bake in flow code, custom pures, examples, or deployment modules.
- It is not rebuilt to publish a new flow.

The flow and its custom pures arrive as a signed CAS bundle. The worker resolves
that bundle from `STORE_URL` at startup using
`WORKER_CONTEXT_FACTORY=julep.execution.bundle_worker:make_context`
and the `JULEP_BUNDLES` / `JULEP_BUNDLE_ALLOWED_SIGNERS` environment block.

## Build context shape

The Dockerfile expects an archived copy of the repo under `julep-v2/` next to
the Dockerfile. This is the same shape used by `tooling/k3d-cad-demo/up.sh`:

```bash
BUILD=/tmp/julep-cad-build
rm -rf "$BUILD" && mkdir -p "$BUILD"
git -C "$REPO_ROOT" archive HEAD --prefix=julep-v2/ | tar -x -C "$BUILD"
cp "$REPO_ROOT/tooling/runtime-image/Dockerfile" "$BUILD/"
docker build -t "$IMAGE" "$BUILD"
```

The important invariant is that the final image keeps only the installed
framework:

```dockerfile
COPY julep-v2 /src/julep-v2
RUN pip install --no-cache-dir uv \
    && pip install --no-cache-dir '/src/julep-v2[dotctx,temporal,store,wasm]' \
    && rm -rf /src/julep-v2
```

## Runtime environment

The image presets:

- `WORKER_CONTEXT_FACTORY=julep.execution.bundle_worker:make_context`
- `WORKER_HEALTH_PORT=8080`

Operators provide:

- `TEMPORAL_ADDRESS`
- `TEMPORAL_TASK_QUEUE`
- `TEMPORAL_NAMESPACE` when not using Temporal's default namespace
- `TEMPORAL_TLS` when connecting with TLS
- `WORKER_GRACEFUL_SHUTDOWN_S`
- `WORKER_MAX_CONCURRENT_ACTIVITIES`
- `WORKER_MAX_CONCURRENT_WORKFLOW_TASKS`
- `STORE_URL`
- `JULEP_BUNDLES`
- `JULEP_BUNDLE_ALLOWED_SIGNERS`
- `JULEP_PURE_NATIVE_DEPS`

`JULEP_PURE_NATIVE_DEPS` is the native-tier grant: a comma-separated list of pure
names allowed to use the uv-managed native venv tier. Empty or unset means no
native grant, so bundle-sourced pures run wasm-only.

The `julep worker` entrypoint exposes `GET /healthz` for liveness
and `GET /readyz` for readiness, and drains gracefully on SIGTERM.

## Execution tiers

Bundle-sourced pures default to the wasm sandbox via the `wasm` extra. The
native tier is opt-in per pure through `JULEP_PURE_NATIVE_DEPS`; it exists for deps
with no supported WASI wheel and builds a per-pure uv-managed venv on the worker
at bundle-resolution time.

See `docs/ops/wasm-tier-runbook.md` for tier operations and
`docs/SPEC.md` section 6.5 for `pureRuntimeRefs` and native grant semantics.

## One image, used by both demos

The k3d demo in `tooling/k3d-cad-demo` and the EKS demo in
`tooling/eks-cad-demo` both build or run this image. There is no second runtime
image definition. The older `tooling/sandbox-k8s/Dockerfile` is a separate
non-generic P3 demo and is out of scope for this runtime image.
