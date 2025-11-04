"""
CLI commands for project management.
"""

from typing import Annotated
from uuid import UUID

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from .app import console, error_console, projects_app
from .utils import get_julep_client


@projects_app.command()
def delete(
    project_id: Annotated[UUID, typer.Option("--id", help="ID of the project to delete")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
):
    """Delete an existing project.
    
    This command will delete a project and all its associations (agents, users, files).
    The default project cannot be deleted.
    """
    if not yes:
        confirm = typer.confirm(f"Are you sure you want to delete project '{project_id}'?")
        if not confirm:
            console.print(Text("Project deletion cancelled.", style="bold yellow"), highlight=True)
            raise typer.Exit()

    try:
        client = get_julep_client()
    except Exception as e:
        error_console.print(Text(f"Error initializing Julep client: {e}", style="bold red"))
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        delete_project_task = progress.add_task("Deleting project...", start=False)
        progress.start_task(delete_project_task)

        try:
            client.projects.delete(project_id)
            progress.update(delete_project_task, completed=True)
        except Exception as e:
            progress.update(delete_project_task, completed=True)
            error_console.print(Text(f"Failed to delete project: {e}", style="bold red"))
            raise typer.Exit(1)

    console.print(Text("Project deleted successfully.", style="bold green"), highlight=True)


@projects_app.command()
def list():
    """List all projects for the current developer."""
    try:
        client = get_julep_client()
    except Exception as e:
        error_console.print(Text(f"Error initializing Julep client: {e}", style="bold red"))
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        list_projects_task = progress.add_task("Fetching projects...", start=False)
        progress.start_task(list_projects_task)

        try:
            projects = client.projects.list()
            progress.update(list_projects_task, completed=True)
        except Exception as e:
            progress.update(list_projects_task, completed=True)
            error_console.print(Text(f"Failed to fetch projects: {e}", style="bold red"))
            raise typer.Exit(1)

    if not projects:
        console.print(Text("No projects found.", style="bold yellow"), highlight=True)
        return

    from rich.table import Table

    table = Table(title="Projects", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=36)
    table.add_column("Name", style="bold")
    table.add_column("Canonical Name", style="dim")
    table.add_column("Created", style="dim")

    for project in projects:
        table.add_row(
            str(project.id),
            project.name,
            project.canonical_name,
            project.created_at.strftime("%Y-%m-%d %H:%M:%S") if project.created_at else "N/A"
        )

    console.print(table, highlight=True) 