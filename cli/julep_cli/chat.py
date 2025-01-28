import json
from typing import Annotated

import typer

from .utils import get_julep_client

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


    client = get_julep_client()

    agent = client.agents.get(agent_id=agent)
    
    session = client.sessions.create(agent=agent.id, situation=situation)

    typer.echo(f"Starting chat with agent '{agent.name}'")

    while True:
        message = typer.prompt("You")
        response = client.sessions.chat(
            session_id=session.id,
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
        )
        typer.echo(f"Agent: {response.choices[0].message.content}")
