from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import weakref
from importlib import metadata
from pathlib import Path
from typing import Any

from wasmtime import Config, Engine, Store
from wasmtime.component import Component, Linker

from ..errors import PureExecutionError

VENDORED_WASM = Path(__file__).resolve().parent / "_wasm" / "executor.wasm"
DEFAULT_FUEL = 2_000_000_000

_EXECUTOR: WasmExecutor | None = None
_EXECUTOR_LOCK = threading.Lock()
_HOST_TRAP_ERROR_TYPES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("all fuel consumed",), "WasmFuelExhausted"),
    (("epoch deadline", "interrupt"), "WasmDeadlineExceeded"),
    (("wasm trap", "unreachable"), "WasmSandboxTrap"),
)


def _stop_epoch_ticker(stop: threading.Event, thread: threading.Thread) -> None:
    """Stop an epoch ticker thread (finalizer target; must not reference the
    executor, so it never keeps it alive)."""
    stop.set()
    if thread.is_alive():
        thread.join(timeout=1.0)


def get_wasm_executor() -> WasmExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        with _EXECUTOR_LOCK:
            if _EXECUTOR is None:
                _EXECUTOR = WasmExecutor()
    return _EXECUTOR


class WasmExecutor:
    """Run bundle-sourced pures in a fresh wasmtime CPython component instance.

    Fuel is always enabled. Epoch interruption is disabled by default; set
    ``COMPOSABLE_WASM_EPOCH_MS`` to enable a best-effort epoch ticker and a
    one-tick deadline per call.
    """

    def __init__(self) -> None:
        self._fuel = int(os.environ.get("COMPOSABLE_WASM_FUEL", str(DEFAULT_FUEL)))
        self._epoch_ms = self._read_epoch_ms()
        self._lock = threading.Lock()
        self._epoch_stop = threading.Event()
        self._epoch_thread: threading.Thread | None = None
        self._engine = self._make_engine()
        self._component = self._load_component()
        self._env_components: dict[str, Component] = {}
        self._env_component_digests: dict[str, str] = {}
        self._linker = Linker(self._engine)
        if self._epoch_ms is not None:
            self._start_epoch_ticker()
            # Tie the ticker's lifetime to this executor: when the executor is
            # collected, stop the thread so it cannot keep calling into a
            # torn-down wasmtime engine (which segfaults). The finalizer binds
            # ONLY the stop event + thread (never ``self``), so it does not keep
            # the executor alive.
            weakref.finalize(self, _stop_epoch_ticker, self._epoch_stop, self._epoch_thread)

    def close(self) -> None:
        """Stop the epoch ticker thread (if any).

        In production the process-global executor lives for the worker's lifetime,
        so this is rarely needed; it exists so short-lived executors (mainly tests)
        can deterministically stop the wall-clock ticker thread before tearing down
        wasmtime objects, instead of waiting for GC. A ticker still calling
        ``increment_epoch()`` while another store/engine is being freed can crash
        the wasmtime native layer.
        """
        self._epoch_stop.set()
        thread = self._epoch_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)

    def register_env_component(self, env_hash: str, component_bytes: bytes) -> None:
        digest = hashlib.sha256(component_bytes).hexdigest()
        with self._lock:
            existing = self._env_component_digests.get(env_hash)
            if existing is not None:
                if existing == digest:
                    return
                raise ValueError(
                    f"conflicting wasm env component bytes for envHash {env_hash}: "
                    f"{existing} != {digest}"
                )
            self._env_components[env_hash] = Component(self._engine, component_bytes)
            self._env_component_digests[env_hash] = digest

    def run(
        self,
        name: str,
        source: str,
        value: Any,
        kwargs: dict[str, Any],
        *,
        env_hash: str | None = None,
    ) -> Any:
        request = {
            "kwargs": kwargs or {},
            "name": name,
            "source": source,
            "value": value,
        }

        try:
            component = self._select_component(name, env_hash)
            raw_request = json.dumps(request, sort_keys=True, separators=(",", ":"))
            # Keep batch 1 conservative: fresh store/instance per call, with a
            # process-local lock around wasmtime component instantiation/calls.
            with self._lock:
                store = Store(self._engine)
                store.set_fuel(self._fuel)
                if self._epoch_ms is not None:
                    store.set_epoch_deadline(1)
                instance = self._linker.instantiate(store, component)
                run = instance.get_func(store, "run")
                if run is None:
                    raise RuntimeError("component export 'run' not found")
                raw_response = run(store, raw_request)
                run.post_return(store)

            response = json.loads(raw_response)
            if not isinstance(response, dict):
                raise RuntimeError("component returned a non-object response")
            if response.get("ok"):
                return response.get("value")
            raise PureExecutionError(
                str(response.get("error_type", "WasmError")),
                str(response.get("error", "")),
                response.get("traceback_tail"),
            )
        except PureExecutionError:
            raise
        except Exception as exc:
            raw_message = str(exc)
            error_type = self._host_error_type(raw_message)
            message = self._host_error_message(error_type, name, raw_message)
            traceback_tail = self._host_traceback_tail(error_type, name, raw_message)
            raise PureExecutionError(error_type, message, traceback_tail) from exc

    def _select_component(self, pure_name: str, env_hash: str | None) -> Component:
        if env_hash is None:
            return self._component
        try:
            return self._env_components[env_hash]
        except KeyError as e:
            raise PureExecutionError(
                "WasmEnvUnavailable",
                f"bundle pure {pure_name!r} requested envHash {env_hash}, "
                "but no env component is registered on this worker",
                [f"WasmEnvUnavailable: {pure_name}", env_hash],
            ) from e

    def _make_engine(self) -> Engine:
        config = Config()
        config.wasm_component_model = True
        config.consume_fuel = True
        if self._epoch_ms is not None:
            try:
                config.epoch_interruption = True
            except AttributeError:
                self._epoch_ms = None
        return Engine(config)

    def _load_component(self) -> Component:
        if not VENDORED_WASM.exists():
            raise FileNotFoundError(f"vendored wasm executor missing: {VENDORED_WASM}")

        cache_path = self._cache_path()
        if cache_path.exists():
            try:
                return Component.deserialize_file(self._engine, str(cache_path))
            except Exception:
                pass

        component = Component.from_file(self._engine, str(VENDORED_WASM))
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(component.serialize())
        except Exception:
            pass
        return component

    def _cache_path(self) -> Path:
        wasm_bytes = VENDORED_WASM.read_bytes()
        digest = hashlib.sha256(wasm_bytes).hexdigest()[:24]
        try:
            wasmtime_version = metadata.version("wasmtime")
        except metadata.PackageNotFoundError:
            wasmtime_version = "unknown"
        # The serialized .cwasm embeds codegen settings: fuel and epoch
        # interruption insert instruction-level checks at compile time. A .cwasm
        # compiled under one Engine Config is NOT safe to run under another —
        # ``deserialize_file`` accepts the mismatch silently and the wasmtime
        # native layer then crashes (SIGILL) at call time, where no Python
        # ``except`` can catch it. So the cache key MUST include every
        # codegen-affecting config flag; otherwise an epoch-enabled executor and
        # a default one would share a file and poison each other.
        config_tag = f"fuel={int(self._fuel > 0)}:epoch={int(self._epoch_ms is not None)}"
        key = hashlib.sha256(
            f"{wasmtime_version}:{digest}:{config_tag}".encode()
        ).hexdigest()[:24]
        cache_dir = Path(os.environ.get("COMPOSABLE_WASM_CACHE_DIR", tempfile.gettempdir()))
        return cache_dir / f"composable_executor_{key}.cwasm"

    def _start_epoch_ticker(self) -> None:
        assert self._epoch_ms is not None
        interval_s = self._epoch_ms / 1000
        stop = self._epoch_stop
        engine = self._engine

        def tick() -> None:
            # Exit promptly when the executor is being collected: a daemon thread
            # that keeps calling increment_epoch() on a torn-down engine segfaults.
            while not stop.wait(interval_s):
                engine.increment_epoch()

        thread = threading.Thread(
            target=tick,
            name="composable-wasm-epoch",
            daemon=True,
        )
        self._epoch_thread = thread
        thread.start()

    @staticmethod
    def _read_epoch_ms() -> int | None:
        raw = os.environ.get("COMPOSABLE_WASM_EPOCH_MS")
        if not raw:
            return None
        epoch_ms = int(raw)
        if epoch_ms <= 0:
            return None
        return epoch_ms

    @staticmethod
    def _host_error_type(message: str) -> str:
        lower_message = message.lower()
        for needles, error_type in _HOST_TRAP_ERROR_TYPES:
            if any(needle in lower_message for needle in needles):
                return error_type
        return "WasmHostError"

    def _host_error_message(self, error_type: str, pure_name: str, raw_message: str) -> str:
        if error_type == "WasmFuelExhausted":
            return (
                f"bundle pure {pure_name!r} exhausted its wasm fuel budget ({self._fuel}); "
                "raise COMPOSABLE_WASM_FUEL or fix the pure's runaway compute"
            )
        if error_type == "WasmDeadlineExceeded":
            return (
                f"bundle pure {pure_name!r} exceeded its wasm epoch deadline "
                "(COMPOSABLE_WASM_EPOCH_MS); the pure ran too long"
            )
        if error_type == "WasmSandboxTrap":
            return (
                f"bundle pure {pure_name!r} trapped in the wasm sandbox: a pure may not "
                "touch the clock, filesystem, network, or any host capability (the wasm "
                "tier runs --stub-wasi with no WASI). If this is not a capability "
                "violation it is a resource limit; see docs/ops/wasm-tier-runbook.md"
            )
        return raw_message

    @staticmethod
    def _host_traceback_tail(error_type: str, pure_name: str, raw_message: str) -> list[str]:
        try:
            lines = [line.strip() for line in raw_message.splitlines() if line.strip()]
            tail = [f"{error_type}: {pure_name}"]
            final_trap_line = next(
                (
                    line
                    for line in reversed(lines)
                    if "wasm trap" in line.lower()
                    or "all fuel consumed" in line.lower()
                    or "interrupt" in line.lower()
                    or "unreachable" in line.lower()
                ),
                None,
            )
            if final_trap_line:
                tail.append(final_trap_line)
            elif lines:
                tail.extend(lines[-2:])
            return tail[:3]
        except Exception:
            return [f"{error_type}: {pure_name}"]
