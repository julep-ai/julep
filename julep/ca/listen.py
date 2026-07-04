from __future__ import annotations

import asyncio
import json
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, TextIO, cast

import typer

from julep.ca.config import load_config
from julep.ca.resolve import ResolvedAgent, resolve_agent
from julep.ca.session_local import (
    event_to_json,
    open_local_session,
    parse_json_or_raw,
)

Poster = Callable[[str, dict[str, Any]], int]


def _read_stdin_lines() -> Iterable[str]:
    yield from sys.stdin


def _post(url: str, payload: dict[str, Any]) -> int:
    body = json.dumps(payload, default=str).encode()
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return int(response.status)
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        typer.echo(f"warning: forward failed: {exc}", err=True)
        return 0


_DEFAULT_POSTER: Poster = _post


async def _listen(
    resolved: ResolvedAgent,
    *,
    forward_to: str,
    in_lines: Iterable[str],
    out: TextIO,
    err: TextIO,
    poster: Poster | None = None,
) -> int:
    handle = await open_local_session(resolved)
    post = poster or _DEFAULT_POSTER
    fatal_seen = False

    async def consume() -> None:
        nonlocal fatal_seen
        async for event in handle.events():
            if event.is_error:
                fatal_seen = fatal_seen or event.fatal
                typer.echo(f"error: {event.reason}", file=err)
            if not event.is_emit:
                continue
            payload = event_to_json(event)
            status = post(forward_to, payload)
            typer.echo(f"-> POST {forward_to} [{status}] seq={event.seq}", file=out)

    consumer = asyncio.create_task(consume())
    try:
        iterator = iter(in_lines)
        sentinel = object()
        while True:
            raw = await asyncio.to_thread(next, iterator, sentinel)
            if raw is sentinel:
                break
            raw_line = cast(str, raw)
            line = raw_line.strip()
            if not line:
                continue
            await handle.send(parse_json_or_raw(line))
    finally:
        await handle.close()
        await consumer

    return 1 if fatal_seen else 0


def listen_command(
    name: str = typer.Argument(..., help="Agent name."),
    forward_to: str = typer.Option(..., "--forward-to", help="URL to receive emitted events."),
) -> None:
    """Forward local session emits to an HTTP endpoint."""
    cfg = load_config(Path("."))
    resolved = resolve_agent(cfg, name)
    if resolved.error is not None:
        typer.echo(f"error: {resolved.error}", err=True)
        raise typer.Exit(2)
    try:
        code = asyncio.run(
            _listen(
                resolved,
                forward_to=forward_to,
                in_lines=_read_stdin_lines(),
                out=sys.stdout,
                err=sys.stderr,
            )
        )
    except Exception as exc:  # noqa: BLE001 - keep CLI porcelain traceback-free.
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from None
    raise typer.Exit(code)
