# Generic code-as-data worker. Note what is NOT here: no flow code, no pures, no
# example modules. The image is built once and never rebuilt to ship a new flow
# — the flow + its custom pures arrive as a signed CAS bundle resolved at
# startup (WORKER_CONTEXT_FACTORY below + CA_BUNDLES in the Deployment env).
FROM python:3.12-slim

COPY julep-v2 /src/julep-v2
# [store] pulls in cryptography for ed25519 bundle-signature verification;
# [wasm] pulls in wasmtime so bundle-sourced pures run in the P3 wasm sandbox
# (the vendored executor.wasm ships inside the wheel via package-data). Drop the
# build context afterwards so the image holds only the installed framework —
# no flow code, no example modules, nothing flow-specific to import.
RUN pip install --no-cache-dir '/src/julep-v2[temporal,store,wasm]' && rm -rf /src/julep-v2

ENV WORKER_CONTEXT_FACTORY=composable_agents.execution.bundle_worker:make_context \
    WORKER_HEALTH_PORT=8080

ENTRYPOINT ["composable-agents", "worker"]
