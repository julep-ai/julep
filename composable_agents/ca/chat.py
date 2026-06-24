from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import TextIO

import typer

from composable_agents.ca.config import load_config
from composable_agents.ca.resolve import ResolvedAgent, resolve_agent
from composable_agents.ca.session_local import open_local_session, parse_json_or_raw
from composable_agents.session import SessionEvent


def _read_stdin_lines() -> Iterable[str]:
    yield from sys.stdin


def render_event(event: SessionEvent) -> str | None:
    if event.is_emit:
        return f"<- {json.dumps(event.payload, default=str)}"
    if event.is_error:
        return f"error: {event.reason}"
    if event.is_closed:
        return f"[closed]{f' {event.reason}' if event.reason else ''}"
    return None


async def _chat(
    resolved: ResolvedAgent,
    *,
    in_lines: Iterable[str],
    out: TextIO,
    err: TextIO,
) -> int:
    handle = await open_local_session(resolved)
    fatal_seen = False

    async def consume() -> None:
        nonlocal fatal_seen
        async for event in handle.events():
            line = render_event(event)
            if line is None:
                continue
            if event.is_error:
                typer.echo(line, file=err)
                fatal_seen = fatal_seen or event.fatal
            else:
                typer.echo(line, file=out)

    consumer = asyncio.create_task(consume())
    try:
        for raw_line in in_lines:
            line = raw_line.strip()
            if not line:
                continue
            await handle.send(parse_json_or_raw(line))
    finally:
        await handle.close()
        await consumer

    return 1 if fatal_seen else 0


def chat_command(
    name: str = typer.Argument(..., help="Agent name."),
    env: str = typer.Option("local", "--env", help="Environment name. Only local is supported."),
) -> None:
    """Open a local chat session and stream emitted replies."""
    cfg = load_config(Path("."))
    if env not in cfg.envs:
        typer.echo(f"error: unknown env {env!r}", err=True)
        raise typer.Exit(2)
    if env != "local":
        typer.echo("error: ca chat currently supports only --env local", err=True)
        raise typer.Exit(2)
    resolved = resolve_agent(cfg, name)
    if resolved.error is not None:
        typer.echo(f"error: {resolved.error}", err=True)
        raise typer.Exit(2)
    try:
        code = asyncio.run(_chat(resolved, in_lines=_read_stdin_lines(), out=sys.stdout, err=sys.stderr))
    except Exception as exc:  # noqa: BLE001 - keep CLI porcelain traceback-free.
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from None
    raise typer.Exit(code)
