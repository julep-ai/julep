# WASM Pure Alpha Runbook

The alpha runs signed, dependency-free Python pures in a fresh Wasmtime CPython
component instance for each call. It supports JSON-compatible inputs and outputs.
Third-party dependencies and the native dependency fallback are not supported.

## Worker setup

- Install the worker with `julep[wasm]`.
- Mount a writable, node-local `JULEP_WASM_CACHE_DIR` when possible.
- Keep artifact-store bundle and signature objects for replay; do not run
  destructive GC against alpha artifacts.
- The worker loads and compiles the base component while resolving the bundle,
  before registering its pures.

## Controls

| Variable | Default | Purpose |
| --- | --- | --- |
| `JULEP_WASM_ENABLED` | `1` | Set to `0` to reject WASM bundle resolution after workers restart. |
| `JULEP_WASM_DEPENDENCIES_ENABLED` | `0` | Experimental dependency backend. Keep disabled for the alpha. |
| `JULEP_WASM_FUEL` | `2000000000` | Deterministic instruction budget per call. |
| `JULEP_WASM_EPOCH_MS` | unset | Optional coarse wall-clock backstop. Keep off on replayable Temporal paths unless its nondeterminism is acceptable. |
| `JULEP_WASM_CACHE_DIR` | OS temp directory | Compiled component cache location. |

Requests and responses are each limited to 4 MiB. Bundled pure source is limited
to 256 KiB.

## Failure handling

- `WasmFuelExhausted`: fix runaway compute or deliberately raise the fuel limit.
- `WasmDeadlineExceeded`: fix long-running compute or review the optional epoch setting.
- `WasmSandboxTrap`: remove filesystem, network, clock, entropy, or other host access.
- `WasmInputTooLarge` / `WasmOutputTooLarge`: reduce the serialized payload.
- `WasmHostError`: verify the worker uses `wasmtime>=45,<46`, contains
  `julep/execution/_wasm/executor.wasm`, and can read its cache directory.

## Rollback

Set `JULEP_WASM_ENABLED=0`, stop admitting new runs to the WASM Temporal task
queue, drain existing workers, and restart the deployment. Do not delete
bundle artifacts needed by existing workflow histories. Never retry a failed
WASM call in the native tier automatically.
