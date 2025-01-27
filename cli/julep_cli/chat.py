from pathlib import Path
from typing import Annotated

import typer

from .app import app


@app.command()
def chat(
    agent: Annotated[str, typer.Option("--agent", "-a", help="Agent ID or name to chat with")],
    situation: Annotated[
        str | None, typer.Option("--situation", "-s", help="Situation to chat about")
    ] = None,
    history: Annotated[
        Path | None,
        typer.Option(
            "--history",
            "-h",
            help="Load chat history from file",
        ),
    ] = None,
    save_history: Annotated[
        Path | None,
        typer.Option(
            "--save-history",
            "-s",
            help="Save chat history to file",
        ),
    ] = None,
):
    """Start an interactive chat session with an agent"""
    # TODO: Implement chat logic
    typer.echo(f"Starting chat with agent '{agent}'")
    if situation:
        typer.echo(f"Context: {situation}")
