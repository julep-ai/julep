import json
from typing import Annotated

import typer

from .app import app


@app.command()
def chat(
    agent: Annotated[
        str,
        typer.Option(
            "--agent",
            "-a",
            help="ID or name of the agent to chat with",
        ),
    ],
    situation: Annotated[
        str | None, typer.Option("--situation", "-s", help="Situation to chat about")
    ] = None,
    settings: Annotated[
        str | None,
        typer.Option("--settings", help="Chat settings as a JSON string", parser=json.loads),
    ] = None,
):
    """
    Initiate an interactive chat session with a specified AI agent.

    The chat session runs in the terminal, allowing real-time conversation with the agent.
    """
    # TODO: Implement chat logic
    typer.echo(f"Starting chat with agent '{agent}'")
    if situation:
        typer.echo(f"Context: {situation}")
    if settings:
        typer.echo(f"Using custom settings: {settings}")
