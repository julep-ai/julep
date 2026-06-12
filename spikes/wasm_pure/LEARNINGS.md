# Wasm Pure Executor Spike

Run from this directory:

```bash
uv sync
uv run python runner.py
```

`runner.py` builds the component if missing, serializes the compiled component cache, runs both
fresh-instance-per-call benchmarks, asserts state-leak probes, records the other adversarial
probes, prints a table, and writes `results.json`. Built artifacts and generated componentize
support files are intentionally gitignored.

## Toolchain

| item | value |
| --- | --- |
| componentize-py | `0.23.0` |
| wasmtime-py host | `45.0.0` |
| host Python | `3.13.5` |
| component Python | `3.14.0`, `sys.platform == "wasi"` |
| component cache | `wasmtime.component.Component.serialize/deserialize_file` |
| host path proven | In-process Python host using `wasmtime.component.Component`, `Linker.add_wasip2()`, fresh `Store`/instance per call, dynamic export lookup for `run` |

Research note: the componentize-py README shows the WIT binding/component flow and notes current
`wasmtime.bindgen` examples require `wasmtime==38.0.0`; that path was not used because
`wasmtime==38.0.0` did not expose the `wasmtime.component` API needed for `Component.serialize`.
`wasmtime==45.0.0` proved the in-process component API and compiled component serialization path.

Pre-initialization: this spike uses the default componentize-py component build path with
`--stub-wasi`. Componentize-py generated and bundled the CPython/WASI component at build time; the
component reports Python 3.14.0 at runtime. I did not use or claim any memory-snapshot restore API.
The cached artifact is a serialized compiled component, not a restorable memory blob.

Payload model: proven. The pure source is passed as a JSON string at runtime, `exec()`ed into a
fresh namespace, and called as `func(value, **static_args)`. The sample pure is not baked into the
component.

## Numbers

120 measured calls per variant, after 5 warmups. Times are milliseconds unless noted.

| metric | value |
| --- | ---: |
| base component size MB | 19.406 |
| compiled artifact size MB | 42.238 |
| one-time componentize build s | 1.811 |
| one-time compile+serialize s | 0.902 |
| Variant A median: deserialize compiled artifact + fresh store/instance + execute | 3.718 |
| Variant A p95 | 4.180 |
| Variant B median: warm worker compiled component + fresh store/instance + execute | 1.555 |
| Variant B p95 | 1.872 |

Breakdown:

| phase | median ms | p95 ms |
| --- | ---: | ---: |
| `Component.deserialize_file` | 1.402 | 1.607 |
| fresh store/instance + execute | 1.561 | 1.822 |
| existing-instance execute only, not fresh | 0.362 | 0.482 |

Budget result: both fresh-per-call variants are under the `<=10ms` p95 budget on this machine.

## Probe Outcomes

State leak through payload exec namespace:

```json
{"call_1":{"ok":true,"value":1},"call_2":{"ok":true,"value":1}}
```

State leak through imported stdlib module state (`json._spike_counter`):

```json
{"call_1":{"ok":true,"value":1},"call_2":{"ok":true,"value":1}}
```

No host-provided WASI:

```json
{"ok":true,"value":{"doubled":42}}
```

Clock:

```json
{
  "import_time": {"ok": true, "value": ["monotonic", "time"]},
  "time_time": {
    "ok": false,
    "error_type": "WasmtimeError",
    "error": "error while executing at wasm backtrace: ... libc.so!wall_clock_now ... Caused by: wasm trap: wasm `unreachable` instruction executed"
  },
  "time_monotonic": {
    "ok": false,
    "error_type": "WasmtimeError",
    "error": "error while executing at wasm backtrace: ... libc.so!monotonic_clock_now ... Caused by: wasm trap: wasm `unreachable` instruction executed"
  }
}
```

Filesystem, with no preopened dirs:

```json
{
  "read_etc_passwd": {
    "ok": false,
    "error_type": "WasmtimeError",
    "error": "error while executing at wasm backtrace: ... libc.so!filesystem_preopens_get_directories ... libc.so!open ... Caused by: wasm trap: wasm `unreachable` instruction executed"
  },
  "write_relative": {
    "ok": false,
    "error_type": "WasmtimeError",
    "error": "error while executing at wasm backtrace: ... libc.so!filesystem_preopens_get_directories ... libc.so!open ... Caused by: wasm trap: wasm `unreachable` instruction executed"
  }
}
```

Network:

```json
{
  "import_socket": {
    "ok": false,
    "error_type": "WasmtimeError",
    "error": "error while executing at wasm backtrace: ... libc.so!filesystem_preopens_get_directories ... PyImport_ImportModuleLevelObject ... Caused by: wasm trap: wasm `unreachable` instruction executed"
  },
  "socket_connect": {
    "ok": false,
    "error_type": "WasmtimeError",
    "error": "error while executing at wasm backtrace: ... PyImport_ImportModuleLevelObject ... Caused by: wasm trap: wasm `unreachable` instruction executed"
  },
  "import_urllib_request": {
    "ok": false,
    "error_type": "WasmtimeError",
    "error": "error while executing at wasm backtrace: ... PyImport_ImportModuleLevelObject ... Caused by: wasm trap: wasm `unreachable` instruction executed"
  },
  "urllib_open": {
    "ok": false,
    "error_type": "WasmtimeError",
    "error": "error while executing at wasm backtrace: ... PyImport_ImportModuleLevelObject ... Caused by: wasm trap: wasm `unreachable` instruction executed"
  }
}
```

The full backtraces are in `results.json` from the last run.

### Sandbox posture

The clock/filesystem/network trap outcomes are a build-time property of the `--stub-wasi`
component: the component carries trapping stubs and needs no host-provided WASI at all. The
`no_host_wasi` probe proves a bare `wasmtime.component.Linker` with a fresh `Store` can instantiate
and run a pure correctly, so denial in this spike does not come from host runtime policy.

The runner keeps `LINKER.add_wasip2()` plus `store.set_wasi(...)` in the default benchmark host path
to preserve the accepted measurement path, but those calls are inert for this stub-built component.
The same host configuration would grant real wall clocks, plus any preopen-granted filesystem
access, to a component built without `--stub-wasi`. For P3, either keep the base component
stub-built, or, if a non-stub component is ever hosted, explicitly exclude `wasi:clocks`,
`wasi:filesystem`, and `wasi:sockets` from the host linker. Stub-built is the recommended default.
Also note that `import time` succeeds and the module is fully importable; only the underlying WASI
syscall traps. P3 exclusion is about syscalls, not imports.

Variant A caveat: `Component.deserialize_file` benefits from a warm OS page cache across the 120
calls; the first call after a true cold worker start will additionally page in the roughly 42 MB
artifact from disk. Cold start has its own separate budget in the plan.

## Recommendation

GO for P1(a) fresh-per-call on the measured small pure: the strict plan variant p95 is 4.180 ms,
with runtime source payloads proven and both state-leak probes passing. Do not treat this as proof
that instance reuse with reset is deterministic; this spike did not prove a reset primitive, and
the existing-instance number is reported only as a non-fresh lower bound. For P3, keep fresh
instance per call as the default, explicitly deny or stub clocks/filesystem/network for pures, and
reserve any reuse-with-reset work for a separate adversarial proof.
