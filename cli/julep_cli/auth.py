import os
from pathlib import Path
from typing import Annotated

import typer

from cli.julep_cli.utils import get_config, save_config

from .app import app


@app.command()
def auth(
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key",
            "-k",
            help="Your Julep API key for authentication",
            prompt="Please enter your Julep API key (find this in your account settings)",
            envvar="JULEP_API_KEY",
        ),
    ] = None,
    environment: Annotated[
        str,
        typer.Option(
            "--environment",
            "-e",
            help="Environment to use (defaults to production)",
        ),
    ] = "production",
):
    """
    Authenticate with the Julep platform.

    Saves your API key to ~/.config/julep/config.yml for use with other commands.
    The API key can be found in your Julep account settings.
    """

    if not api_key:
        typer.echo("No API key provided", err=True)
        raise typer.Exit(1)

    config = get_config()
    config["api_key"] = api_key
    config["environment"] = environment
    save_config(config)

    typer.echo(f"Successfully authenticated with {environment} environment!")
