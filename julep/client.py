"""Small synchronous client for the Julep execution control plane."""

from __future__ import annotations

from typing import Any, cast

import httpx

from julep.projection import EventType, ProjectionEvent


class JulepClientError(RuntimeError):
    def __init__(self, status_code: int, detail: Any) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"julep API error {status_code}: {detail}")


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
        headers = {**self._headers, **dict(kwargs.pop("headers", {}))}
        response = self._client.request(method, path, headers=headers, **kwargs)
        if response.status_code not in expect:
            try:
                payload = response.json()
                detail = payload.get("detail", payload) if isinstance(payload, dict) else payload
            except ValueError:
                detail = response.text
            raise JulepClientError(response.status_code, detail)
        return response

    def health(self) -> dict[str, Any]:
        return cast(dict[str, Any], self._request("GET", "/v1/health").json())

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
        queue_lanes: dict[str, str] | None = None,
        idempotency_key: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        if not idempotency_key and not run_id:
            raise ValueError("start_run requires idempotency_key or run_id")
        body: dict[str, Any] = {"pipeline": pipeline, "input": input}
        for key, value in (
            ("release", release),
            ("sessionId", session_id),
            ("principal", principal),
            ("queueLanes", queue_lanes),
            ("runId", run_id),
        ):
            if value is not None:
                body[key] = value
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else {}
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

    def get_result(self, run_id: str, *, wait_s: float = 0.0) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            self._request(
                "GET", f"/v1/runs/{run_id}/result", params={"wait_s": wait_s}
            ).json(),
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
        return [
            ProjectionEvent(
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
            for row in self.iter_events(run_id)
        ]

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


__all__ = ["JulepClient", "JulepClientError"]
