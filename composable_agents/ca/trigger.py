from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import TextIO

import typer

from composable_agents.ca.chat import render_event
from composable_agents.ca.config import load_config
from composable_agents.ca.resolve import ResolvedAgent, resolve_agent
from composable_agents.ca.session_local import open_local_session, parse_json_or_raw


async def _trigger(
    resolved: ResolvedAgent,
    event: str,
    *,
    channel: str,
    out: TextIO,
    err: TextIO,
) -> int:
    handle = await open_local_session(resolved)
    agen = handle.events()
    fatal_seen = False
    turn_done = False
    try:
        await handle.send(parse_json_or_raw(event), channel=channel)
        while not turn_done:
            session_event = await agen.__anext__()
            line = render_event(session_event)
            if line is not None:
                typer.echo(line, file=err if session_event.is_error else out)
            if session_event.is_error:
                fatal_seen = fatal_seen or session_event.fatal
                if session_event.fatal:
                    break
            if session_event.is_closed:
                return 1 if fatal_seen else 0
            turn_done = session_event.is_turn and session_event.turn == "done"
    finally:
        await handle.close()

    async for session_event in agen:
        line = render_event(session_event)
        if line is not None:
            typer.echo(line, file=err if session_event.is_error else out)
        if session_event.is_error:
            fatal_seen = fatal_seen or session_event.fatal

    return 1 if fatal_seen else 0


def trigger_command(
    name: str = typer.Argument(..., help="Agent name."),
    event: str = typer.Argument(..., help="JSON event payload, or a raw string."),
    channel: str = typer.Option("in", "--channel", help="Input channel to send to."),
) -> None:
    """Send one event to a local session and print emitted replies."""
    cfg = load_config(Path("."))
    resolved = resolve_agent(cfg, name)
    if resolved.error is not None:
        typer.echo(f"error: {resolved.error}", err=True)
        raise typer.Exit(2)
    try:
        code = asyncio.run(_trigger(resolved, event, channel=channel, out=sys.stdout, err=sys.stderr))
    except Exception as exc:  # noqa: BLE001 - keep CLI porcelain traceback-free.
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from None
    raise typer.Exit(code)
