import json
from typing import Annotated

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from .app import app, console, error_console
from .utils import get_julep_client


@app.command()
def chat(
    agent: Annotated[
        str,
        typer.Option(
            "--agent",
            "-a",
            help="ID the agent to chat with",
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

    client = get_julep_client()

    try:
        agent = client.agents.get(agent_id=agent)
    except Exception as e:
        error_console.print(Text(f"Error: {e}", style="bold red"), highlight=True)
        raise typer.Exit(1)

    session = client.sessions.create(agent=agent.id, situation=situation)

    console.print(
        Panel(
            Text(f"Starting chat with agent '{agent.name}'", style="bold green"),
            title="Chat Session",
        )
    )

    while True:
        message = typer.prompt("You")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Waiting for agent response...", start=False)
            progress.start_task(task)

            response = client.sessions.chat(
                session_id=session.id,
                messages=[
                    {
                        "role": "user",
                        "content": message,
                    }
                ],
            )

        console.print(
            Panel(
                Text(response.choices[0].message.content, style="bold blue"),
                title="Agent Response",
            )
        )
