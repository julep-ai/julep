from typing import Annotated

import typer

from .app import app, console, error_console
from .utils import get_config, save_config


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
            prompt="Please enter the environment to use (defaults to production)",
        ),
    ] = "production",
):
    """
    Authenticate with the Julep platform.

    Saves your API key to ~/.config/julep/config.yml for use with other commands.
    The API key can be found in your Julep account settings.
    """

    if not api_key:
        error_console.print("[red]No API key provided[/red]", err=True)
        raise typer.Exit(1)

    config = get_config()
    config["api_key"] = api_key
    config["environment"] = environment
    save_config(config)

    console.print(f"Successfully authenticated with [green]{environment}[/green] environment!")
