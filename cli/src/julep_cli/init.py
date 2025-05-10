import io
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Annotated

import requests
import typer
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from stringcase import titlecase

from .app import app
from .templates import templates
from .utils import confirm_proceed, console, error_console, get_directory_tree, to_relative
from .wrapper import DocStrEnum

template_names = [t["name"] for t in templates]
template_descriptions = [
    t["config"].get("description", titlecase(t["name"])) for t in templates
]


repo_url = os.getenv("JULEP_LIBRARY_REPO_URL", "https://github.com/julep-ai/library")
branch = os.getenv("JULEP_LIBRARY_BRANCH", "main")
template_url = f"{repo_url}/archive/refs/heads/{branch}.zip"

TemplateEnum = DocStrEnum(
    "JulepTemplate",
    zip(template_names, zip(template_names, template_descriptions)),
)


@app.command()
def init(
    template: Annotated[
        TemplateEnum,
        typer.Option(
            "--template",
            "-t",
            help="Name of the template to use from the library repository (or 'empty' for an empty project)",
            case_sensitive=False,
        ),
        {"default": lambda: template_names[0]},
    ],
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Destination directory for the initialized project (default: current directory)",
        ),
        {"default": Path.cwd()},
    ],
    yes: Annotated[
        bool,
        typer.Option(help="Skip confirmation prompt"),
    ] = False,
):
    """
    Initialize a new Julep project.

    This command downloads a predefined template from the library repository.
    The default template is "hello-world".

    Steps performed:
      1. Downloads and extracts the specified template folder.
      2. Validates that a 'julep.yaml' file exists.
      3. Displays a directory tree of the created project.
      4. Prints instructions to change directory into the project,
         and optionally opens a new shell there.
    """

    julep_yaml = path / "julep.yaml"
    if julep_yaml.exists():
        error_console.print(
            Text(
                "Error: 'julep.yaml' already exists in the project directory", style="bold red"
            ),
            highlight=True,
        )
        raise typer.Exit(1)

    if not yes:
        confirm_proceed(
            f"This will initialize a new Julep project in '{path}' with template '{template}'. Proceed?",
        )

    with console.status("Downloading template..."):
        response = requests.get(template_url)

    if response.status_code != 200:
        error_console.print(
            Text(f"Failed to download template: {response.status_code}", style="bold red"),
            highlight=True,
        )
        raise typer.Exit(1)

    tmp = tempfile.mkdtemp()
    template_folder = f"{tmp}/{template}/"

    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(template_folder)

    except zipfile.BadZipFile as e:
        error_console.print(
            Text(f"Failed to extract template: {e}", style="bold red"),
            highlight=True,
        )
        raise typer.Exit(1)

    extracted_template_path = Path(template_folder) / f"library-{branch}/{template}"
    final_destination = Path.resolve(path)

    try:
        # Warn the user if final_destination exists and is not empty (files will be merged)
        if (
            not yes
            and final_destination.exists()
            and any(final_destination.iterdir())
        ):
            confirm_proceed(
                f"Warning: The directory '{to_relative(final_destination)}' already exists and is not empty. Do you want to proceed?",
            )

        final_destination.mkdir(parents=True, exist_ok=True)

        # Copy contents of the template directory instead of the directory itself
        shutil.copytree(
            extracted_template_path, final_destination, dirs_exist_ok=True, symlinks=True
        )

    finally:
        shutil.rmtree(tmp)

    console.print(
        Text(
            f"Successfully initialized new Julep project with template '{template}' in {to_relative(final_destination)}",
            style="bold green",
        ),
        highlight=True,
    )

    if final_destination != Path.cwd():
        cd_instruction = f"cd {to_relative(final_destination)}"
        console.print(
            Text(
                f"To start working on your project, run: `{cd_instruction}`", style="bold green"
            ),
            highlight=True,
        )

    # Get the readme file
    readme_path = final_destination / "README.md"

    if typer.confirm(f"Would you like to read the {template} README?", default=True):
        with console.pager():
            console.print(get_directory_tree(final_destination), soft_wrap=True, highlight=True)

            if readme_path.exists():
                readme_content = readme_path.read_text()
                markdown = Markdown(readme_content)
                console.print(
                    Panel(markdown, title=Text("Project README", style="bold blue")),
                    highlight=True,
                    soft_wrap=True,
                )
