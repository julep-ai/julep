"""Sync and async clients for the Julep execution control plane."""

from __future__ import annotations

import math
import time
from collections.abc import Mapping
from typing import Any, Literal, cast

import httpx

from julep.projection import EventType, ProjectionEvent


class JulepClientError(RuntimeError):
    def __init__(self, status_code: int, detail: Any) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"julep API error {status_code}: {detail}")


class JulepRunError(RuntimeError):
    """Base class for execution-adoption errors raised by wait helpers."""

    def __init__(self, message: str, *, run_id: str | None) -> None:
        self.run_id = run_id
        super().__init__(message)


class JulepRunProtocolError(JulepRunError):
    """The control plane returned a malformed run or result envelope."""


class JulepRunTimeout(JulepRunError):
    """A run did not finish within the caller's bounded wait."""

    def __init__(self, run_id: str, deadline_s: float) -> None:
        self.deadline_s = deadline_s
        super().__init__(
            f"julep run {run_id} exceeded the {deadline_s:g}s deadline",
            run_id=run_id,
        )


class JulepRunFailed(JulepRunError):
    """A run reached a non-success terminal status."""

    def __init__(self, run_id: str, status: str, error: Any = None) -> None:
        self.status = status
        self.error = error
        self.detail = self.error
        detail = f": {self.error}" if self.error is not None else ""
        super().__init__(
            f"julep run {run_id} ended in terminal status {status!r}{detail}",
            run_id=run_id,
        )


_FAILED_STATUSES = frozenset({"failed", "canceled", "terminated", "start_failed"})
_PENDING = object()


def _error_detail(response: httpx.Response) -> Any:
    try:
        payload = response.json()
        return payload.get("detail", payload) if isinstance(payload, dict) else payload
    except ValueError:
        return response.text


def _checked_response(
    response: httpx.Response, expect: tuple[int, ...]
) -> httpx.Response:
    if response.status_code not in expect:
        raise JulepClientError(response.status_code, _error_detail(response))
    return response


def _request_headers(
    defaults: Mapping[str, str], extra: Mapping[str, str] | None
) -> dict[str, str]:
    return {**defaults, **dict(extra or {})}


def _start_request(
    *,
    pipeline: str,
    input: Any,
    release: str | None,
    session_id: str | None,
    principal: dict[str, Any] | None,
    secrets: dict[str, str] | None,
    mcp_preflight: Literal["pin", "names", "off"] | None,
    queue_lanes: dict[str, str] | None,
    idempotency_key: str | None,
    run_id: str | None,
) -> tuple[dict[str, Any], dict[str, str]]:
    if not idempotency_key and not run_id:
        raise ValueError("start_run requires idempotency_key or run_id")
    body: dict[str, Any] = {"pipeline": pipeline, "input": input}
    for key, value in (
        ("release", release),
        ("sessionId", session_id),
        ("principal", principal),
        ("secrets", secrets),
        ("mcpPreflight", mcp_preflight),
        ("queueLanes", queue_lanes),
        ("runId", run_id),
    ):
        if value is not None:
            body[key] = value
    headers = {"Idempotency-Key": idempotency_key} if idempotency_key else {}
    return body, headers


def _validate_wait(deadline_s: float, poll_wait_s: float) -> tuple[float, float]:
    deadline = float(deadline_s)
    poll_wait = float(poll_wait_s)
    if not math.isfinite(deadline) or deadline < 0:
        raise ValueError("deadline_s must be a finite non-negative number")
    if not math.isfinite(poll_wait) or poll_wait <= 0:
        raise ValueError("poll_wait_s must be a finite positive number")
    return deadline, min(poll_wait, 60.0)


def _started_run_id(started: Mapping[str, Any]) -> str:
    value = started.get("run_id")
    if not isinstance(value, str) or not value:
        raise JulepRunProtocolError(
            "julep start_run response did not contain a non-empty run_id",
            run_id=None,
        )
    return value


def _resolve_result(envelope: Mapping[str, Any], expected_run_id: str) -> Any:
    run = envelope.get("run")
    if not isinstance(run, Mapping):
        raise JulepRunProtocolError(
            "julep result response did not contain a run object",
            run_id=expected_run_id,
        )
    run_id = run.get("run_id")
    if run_id is not None and run_id != expected_run_id:
        raise JulepRunProtocolError(
            "julep result response run_id did not match the requested run",
            run_id=expected_run_id,
        )
    status = run.get("status")
    if status == "completed":
        if "result" not in envelope:
            raise JulepRunProtocolError(
                "completed julep result response did not contain result",
                run_id=expected_run_id,
            )
        return envelope["result"]
    if isinstance(status, str) and status in _FAILED_STATUSES:
        raise JulepRunFailed(
            expected_run_id,
            status,
            run.get("error", run.get("detail")),
        )
    return _PENDING


def _projection_event(row: Mapping[str, Any]) -> ProjectionEvent:
    return ProjectionEvent(
        event_id=str(row["event_id"]),
        type=EventType(row["type"]),
        node=str(row["node"]),
        cid=str(row["cid"]),
        ts=float(row["ts"]),
        causes=tuple(str(cause) for cause in (row.get("causes") or ())),
        value_ref=cast(str | None, row.get("value_ref")),
        shape=cast(str | None, row.get("shape")),
        cost=cast(float | None, row.get("cost")),
        error=cast(str | None, row.get("error")),
        attrs=dict(row.get("attrs") or {}),
    )


class JulepClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        if client is None:
            if not base_url:
                raise ValueError("base_url is required when client is not provided")
            self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)
            self._owns = True
        else:
            self._client = client
            self._owns = False
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def _request(
        self,
        method: str,
        path: str,
        *,
        expect: tuple[int, ...] = (200, 201, 202),
        **kwargs: Any,
    ) -> httpx.Response:
        headers = _request_headers(self._headers, kwargs.pop("headers", None))
        response = self._client.request(method, path, headers=headers, **kwargs)
        return _checked_response(response, expect)

    def health(self) -> dict[str, Any]:
        return cast(dict[str, Any], self._request("GET", "/v1/health").json())

    def publish_release(self, manifest_bytes: bytes) -> dict[str, Any]:
        """Register a published release manifest with the control plane.

        POSTs the raw manifest bytes to ``/v1/releases`` (admin-only). Returns
        the stored release row (201 created, 200 if already present).
        """
        return cast(
            dict[str, Any],
            self._request(
                "POST",
                "/v1/releases",
                content=manifest_bytes,
                headers={"Content-Type": "application/json"},
            ).json(),
        )

    def list_runs(self, *, cursor: str | None = None, limit: int = 50) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        return cast(dict[str, Any], self._request("GET", "/v1/runs", params=params).json())

    def get_run(self, run_id: str) -> dict[str, Any]:
        return cast(dict[str, Any], self._request("GET", f"/v1/runs/{run_id}").json())

    def start_run(
        self,
        *,
        pipeline: str,
        input: Any = None,
        release: str | None = None,
        session_id: str | None = None,
        principal: dict[str, Any] | None = None,
        secrets: dict[str, str] | None = None,
        mcp_preflight: Literal["pin", "names", "off"] | None = None,
        queue_lanes: dict[str, str] | None = None,
        idempotency_key: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        body, headers = _start_request(
            pipeline=pipeline,
            input=input,
            release=release,
            session_id=session_id,
            principal=principal,
            secrets=secrets,
            mcp_preflight=mcp_preflight,
            queue_lanes=queue_lanes,
            idempotency_key=idempotency_key,
            run_id=run_id,
        )
        return cast(
            dict[str, Any],
            self._request("POST", "/v1/runs", json=body, headers=headers).json(),
        )

    def cancel_run(self, run_id: str) -> dict[str, Any]:
        return cast(
            dict[str, Any], self._request("POST", f"/v1/runs/{run_id}/cancel").json()
        )

    def terminate_run(self, run_id: str) -> dict[str, Any]:
        return cast(
            dict[str, Any], self._request("POST", f"/v1/runs/{run_id}/terminate").json()
        )

    def get_result(
        self,
        run_id: str,
        *,
        wait_s: float = 0.0,
        request_timeout_s: float | None = None,
    ) -> dict[str, Any]:
        request_options: dict[str, Any] = {}
        if request_timeout_s is not None:
            request_options["timeout"] = request_timeout_s
        return cast(
            dict[str, Any],
            self._request(
                "GET",
                f"/v1/runs/{run_id}/result",
                params={"wait_s": wait_s},
                **request_options,
            ).json(),
        )

    def wait_for_run(
        self,
        run_id: str,
        *,
        deadline_s: float = 300.0,
        poll_wait_s: float = 20.0,
    ) -> Any:
        """Wait for ``run_id`` and return its unwrapped result payload."""

        deadline_seconds, poll_wait = _validate_wait(deadline_s, poll_wait_s)
        deadline = time.monotonic() + deadline_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise JulepRunTimeout(run_id, deadline_seconds)
            try:
                envelope = self.get_result(
                    run_id,
                    wait_s=min(poll_wait, remaining),
                    request_timeout_s=remaining,
                )
            except httpx.TimeoutException as exc:
                raise JulepRunTimeout(run_id, deadline_seconds) from exc
            result = _resolve_result(envelope, run_id)
            if result is not _PENDING:
                return result

    def start_and_wait(
        self,
        *,
        pipeline: str,
        input: Any = None,
        release: str | None = None,
        session_id: str | None = None,
        principal: dict[str, Any] | None = None,
        secrets: dict[str, str] | None = None,
        mcp_preflight: Literal["pin", "names", "off"] | None = None,
        queue_lanes: dict[str, str] | None = None,
        idempotency_key: str | None = None,
        run_id: str | None = None,
        deadline_s: float = 300.0,
        poll_wait_s: float = 20.0,
    ) -> Any:
        """Submit idempotently, wait within a deadline, and unwrap the result."""

        started = self.start_run(
            pipeline=pipeline,
            input=input,
            release=release,
            session_id=session_id,
            principal=principal,
            secrets=secrets,
            mcp_preflight=mcp_preflight,
            queue_lanes=queue_lanes,
            idempotency_key=idempotency_key,
            run_id=run_id,
        )
        return self.wait_for_run(
            _started_run_id(started),
            deadline_s=deadline_s,
            poll_wait_s=poll_wait_s,
        )

    def run_and_wait(
        self,
        *,
        pipeline: str,
        input: Any = None,
        release: str | None = None,
        session_id: str | None = None,
        principal: dict[str, Any] | None = None,
        secrets: dict[str, str] | None = None,
        queue_lanes: dict[str, str] | None = None,
        idempotency_key: str | None = None,
        run_id: str | None = None,
        deadline_s: float = 300.0,
        poll_wait_s: float = 20.0,
    ) -> Any:
        """Alias for :meth:`start_and_wait` with the same typed contract."""

        return self.start_and_wait(
            pipeline=pipeline,
            input=input,
            release=release,
            session_id=session_id,
            principal=principal,
            secrets=secrets,
            queue_lanes=queue_lanes,
            idempotency_key=idempotency_key,
            run_id=run_id,
            deadline_s=deadline_s,
            poll_wait_s=poll_wait_s,
        )

    def read_events(
        self,
        run_id: str,
        *,
        after: int | str = 0,
        limit: int = 500,
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            self._request(
                "GET",
                f"/v1/runs/{run_id}/events",
                params={"after": after, "limit": limit},
                headers={"Accept": "application/json"},
            ).json(),
        )

    def iter_events(self, run_id: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        cursor: int | str = 0
        for _page in range(10_000):
            data = self.read_events(run_id, after=cursor)
            items = data.get("items", [])
            if not isinstance(items, list):
                raise ValueError("events response items must be a list")
            events.extend(cast(list[dict[str, Any]], items))
            next_cursor = data.get("next_cursor")
            if next_cursor is None:
                return events
            if next_cursor == cursor:
                raise ValueError("events response cursor did not advance")
            cursor = cast(str, next_cursor)
        raise ValueError("events response exceeded page limit")

    def projection_events(self, run_id: str) -> list[ProjectionEvent]:
        return [_projection_event(row) for row in self.iter_events(run_id)]

    def close(self) -> None:
        if self._owns:
            self._client.close()

    def __enter__(self) -> JulepClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> None:
        self.close()


class AsyncJulepClient:
    """Asynchronous control-plane client with parity with :class:`JulepClient`."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        if client is None:
            if not base_url:
                raise ValueError("base_url is required when client is not provided")
            self._client = httpx.AsyncClient(
                base_url=base_url.rstrip("/"), timeout=timeout
            )
            self._owns = True
        else:
            self._client = client
            self._owns = False
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        expect: tuple[int, ...] = (200, 201, 202),
        **kwargs: Any,
    ) -> httpx.Response:
        headers = _request_headers(self._headers, kwargs.pop("headers", None))
        response = await self._client.request(method, path, headers=headers, **kwargs)
        return _checked_response(response, expect)

    async def health(self) -> dict[str, Any]:
        return cast(dict[str, Any], (await self._request("GET", "/v1/health")).json())

    async def publish_release(self, manifest_bytes: bytes) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            (
                await self._request(
                    "POST",
                    "/v1/releases",
                    content=manifest_bytes,
                    headers={"Content-Type": "application/json"},
                )
            ).json(),
        )

    async def list_runs(
        self, *, cursor: str | None = None, limit: int = 50
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        return cast(
            dict[str, Any],
            (await self._request("GET", "/v1/runs", params=params)).json(),
        )

    async def get_run(self, run_id: str) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            (await self._request("GET", f"/v1/runs/{run_id}")).json(),
        )

    async def start_run(
        self,
        *,
        pipeline: str,
        input: Any = None,
        release: str | None = None,
        session_id: str | None = None,
        principal: dict[str, Any] | None = None,
        secrets: dict[str, str] | None = None,
        mcp_preflight: Literal["pin", "names", "off"] | None = None,
        queue_lanes: dict[str, str] | None = None,
        idempotency_key: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        body, headers = _start_request(
            pipeline=pipeline,
            input=input,
            release=release,
            session_id=session_id,
            principal=principal,
            secrets=secrets,
            mcp_preflight=mcp_preflight,
            queue_lanes=queue_lanes,
            idempotency_key=idempotency_key,
            run_id=run_id,
        )
        return cast(
            dict[str, Any],
            (
                await self._request(
                    "POST", "/v1/runs", json=body, headers=headers
                )
            ).json(),
        )

    async def cancel_run(self, run_id: str) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            (await self._request("POST", f"/v1/runs/{run_id}/cancel")).json(),
        )

    async def terminate_run(self, run_id: str) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            (await self._request("POST", f"/v1/runs/{run_id}/terminate")).json(),
        )

    async def get_result(
        self,
        run_id: str,
        *,
        wait_s: float = 0.0,
        request_timeout_s: float | None = None,
    ) -> dict[str, Any]:
        request_options: dict[str, Any] = {}
        if request_timeout_s is not None:
            request_options["timeout"] = request_timeout_s
        return cast(
            dict[str, Any],
            (
                await self._request(
                    "GET",
                    f"/v1/runs/{run_id}/result",
                    params={"wait_s": wait_s},
                    **request_options,
                )
            ).json(),
        )

    async def wait_for_run(
        self,
        run_id: str,
        *,
        deadline_s: float = 300.0,
        poll_wait_s: float = 20.0,
    ) -> Any:
        deadline_seconds, poll_wait = _validate_wait(deadline_s, poll_wait_s)
        deadline = time.monotonic() + deadline_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise JulepRunTimeout(run_id, deadline_seconds)
            try:
                envelope = await self.get_result(
                    run_id,
                    wait_s=min(poll_wait, remaining),
                    request_timeout_s=remaining,
                )
            except httpx.TimeoutException as exc:
                raise JulepRunTimeout(run_id, deadline_seconds) from exc
            result = _resolve_result(envelope, run_id)
            if result is not _PENDING:
                return result

    async def start_and_wait(
        self,
        *,
        pipeline: str,
        input: Any = None,
        release: str | None = None,
        session_id: str | None = None,
        principal: dict[str, Any] | None = None,
        secrets: dict[str, str] | None = None,
        mcp_preflight: Literal["pin", "names", "off"] | None = None,
        queue_lanes: dict[str, str] | None = None,
        idempotency_key: str | None = None,
        run_id: str | None = None,
        deadline_s: float = 300.0,
        poll_wait_s: float = 20.0,
    ) -> Any:
        started = await self.start_run(
            pipeline=pipeline,
            input=input,
            release=release,
            session_id=session_id,
            principal=principal,
            secrets=secrets,
            mcp_preflight=mcp_preflight,
            queue_lanes=queue_lanes,
            idempotency_key=idempotency_key,
            run_id=run_id,
        )
        return await self.wait_for_run(
            _started_run_id(started),
            deadline_s=deadline_s,
            poll_wait_s=poll_wait_s,
        )

    async def run_and_wait(
        self,
        *,
        pipeline: str,
        input: Any = None,
        release: str | None = None,
        session_id: str | None = None,
        principal: dict[str, Any] | None = None,
        secrets: dict[str, str] | None = None,
        queue_lanes: dict[str, str] | None = None,
        idempotency_key: str | None = None,
        run_id: str | None = None,
        deadline_s: float = 300.0,
        poll_wait_s: float = 20.0,
    ) -> Any:
        return await self.start_and_wait(
            pipeline=pipeline,
            input=input,
            release=release,
            session_id=session_id,
            principal=principal,
            secrets=secrets,
            queue_lanes=queue_lanes,
            idempotency_key=idempotency_key,
            run_id=run_id,
            deadline_s=deadline_s,
            poll_wait_s=poll_wait_s,
        )

    async def read_events(
        self,
        run_id: str,
        *,
        after: int | str = 0,
        limit: int = 500,
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            (
                await self._request(
                    "GET",
                    f"/v1/runs/{run_id}/events",
                    params={"after": after, "limit": limit},
                    headers={"Accept": "application/json"},
                )
            ).json(),
        )

    async def iter_events(self, run_id: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        cursor: int | str = 0
        for _page in range(10_000):
            data = await self.read_events(run_id, after=cursor)
            items = data.get("items", [])
            if not isinstance(items, list):
                raise ValueError("events response items must be a list")
            events.extend(cast(list[dict[str, Any]], items))
            next_cursor = data.get("next_cursor")
            if next_cursor is None:
                return events
            if next_cursor == cursor:
                raise ValueError("events response cursor did not advance")
            cursor = cast(str, next_cursor)
        raise ValueError("events response exceeded page limit")

    async def projection_events(self, run_id: str) -> list[ProjectionEvent]:
        return [_projection_event(row) for row in await self.iter_events(run_id)]

    async def aclose(self) -> None:
        if self._owns:
            await self._client.aclose()

    async def close(self) -> None:
        await self.aclose()

    async def __aenter__(self) -> AsyncJulepClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> None:
        await self.aclose()


__all__ = [
    "AsyncJulepClient",
    "JulepClient",
    "JulepClientError",
    "JulepRunError",
    "JulepRunFailed",
    "JulepRunProtocolError",
    "JulepRunTimeout",
]
