# GENERIC code-as-data worker runtime image.
#
# This image holds no flow code, no pures, and no example modules. It is built
# once at framework cadence and is never rebuilt to ship a new flow. The flow
# and its custom pures arrive as a signed CAS bundle resolved from STORE_URL at
# startup (WORKER_CONTEXT_FACTORY below plus JULEP_BUNDLES and
# JULEP_BUNDLE_ALLOWED_SIGNERS in the Deployment env).
#
# The `julep worker` entrypoint provides /healthz, /readyz, and
# graceful SIGTERM drain. `uv` is present for the P4 native dependency tier: a
# per-pure uv-managed venv is built on the worker at bundle-resolution time only
# for off-WASI-wheel deps explicitly granted by JULEP_PURE_NATIVE_DEPS. The default
# wasm tier does not need uv, so uv stays dormant unless a native grant is set.
FROM python:3.12-slim

COPY julep-v2 /src/julep-v2
# Install the julep framework with production runtime extras:
# [temporal] for durable workers, [store] for S3 CAS and ed25519 signature
# verification, and [wasm] for wasmtime plus the vendored executor.wasm package
# data. Drop the build context afterwards so the final image contains only the
# installed framework.
RUN pip install --no-cache-dir uv \
    && pip install --no-cache-dir '/src/julep-v2[temporal,store,wasm]' \
    && rm -rf /src/julep-v2

ENV WORKER_CONTEXT_FACTORY=julep.execution.bundle_worker:make_context \
    WORKER_HEALTH_PORT=8080

ENTRYPOINT ["julep", "worker"]
