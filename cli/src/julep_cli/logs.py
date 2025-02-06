import json
from typing import Annotated, ClassVar

import typer
from julep.resources.executions.transitions import Transition
from rich.box import HEAVY
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

# New imports for Textual Log TUI functionality
from textual.app import App
from textual.binding import Binding
from textual.widgets import Header, Static
from textual.widgets import Log as TextLog

from .app import app, console, error_console
from .utils import get_julep_client, manage_db_attribute


# New TUI app using Textual's Log widget to display transitions in tailing mode
class TransitionLogApp(App):
    # Add a binding for Ctrl+C to quit
    BINDINGS: ClassVar[list[Binding]] = [
        Binding(
            "ctrl+c",
            "quit",
            "Quit",
            tooltip="Quit the app and return to the command prompt.",
            show=False,
            priority=True,
        )
    ]
    TITLE = "Transition Log"

    def __init__(self, client, execution_id, initial_transitions, **kwargs):
        # Set the app title so Header() can pick it up
        super().__init__(**kwargs)
        self.client = client
        self.execution_id = execution_id
        self.transitions = initial_transitions
        self.log_widget = None

    def compose(self):
        # Yield a header; Header() will display the app's title (set above)
        yield Header()

        # Create the Log widget
        self.log_widget = TextLog(highlight=True)
        yield self.log_widget

        # Add a footer with an exit message
        yield Static("Press Ctrl+C to exit")

    async def on_mount(self) -> None:
        # Display the initial transitions in reversed order
        for transition in reversed(self.transitions):
            self.log_widget.write(
                f"{transition.type}:\n{json.dumps(transition.output, indent=4)}\n\n"
            )
        # Set up a periodic callback every 1 second to check for new transitions
        self.set_interval(1, self.fetch_new_transitions)

    async def fetch_new_transitions(self) -> None:
        fetched_transitions = self.client.executions.transitions.list(
            execution_id=self.execution_id
        ).items
        # Calculate the number of new transitions
        delta = len(fetched_transitions) - len(self.transitions)
        if delta > 0:
            new_transitions = fetched_transitions[:delta]
            for transition in reversed(new_transitions):
                self.log_widget.write(
                    f"{transition.type}:\n{json.dumps(transition.output, indent=4)}\n\n"
                )
            self.transitions = fetched_transitions

        # If a terminal state is reached, display a final message and keep the app open.
        if (
            self.transitions
            and self.transitions[0].type in ["finish", "cancelled", "error"]
            and not hasattr(self, "_completion_message_shown")
        ):
            self.log_widget.write("\nExecution complete.")
            self._completion_message_shown = True


@app.command()
def logs(
    execution_id: Annotated[
        str | None, typer.Option("--execution-id", "-e", help="ID of the execution to log")
    ] = None,
    tailing: Annotated[
        bool, typer.Option("--tail", "-t", help="Whether to tail the logs")
    ] = False,
):
    """
    Log the output of an execution.
    """

    # Update or fetch the execution_id from the database
    execution_id = manage_db_attribute("execution_id", execution_id)

    transitions_table = Table(
        title="Execution Transitions",
        box=HEAVY,  # border between cells
        show_lines=True,  # Adds lines between rows
        show_header=True,
        header_style="bold magenta",
    )

    transitions_table.add_column(
        "Transition Type",
        style="bold cyan",
        no_wrap=True,
        justify="center",
        vertical="middle",
    )
    transitions_table.add_column(
        "Transition Output",
        style="green",
    )

    def display_transitions(transitions: list[Transition]):
        for transition in reversed(transitions):
            transitions_table.add_row(transition.type, json.dumps(transition.output, indent=4))
        console.print(transitions_table, highlight=True)

    client = get_julep_client()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        try:
            fetch_transitions = progress.add_task(
                description="Fetching transitions", total=None
            )
            progress.start_task(fetch_transitions)

            transitions = client.executions.transitions.list(execution_id=execution_id).items
        except Exception as e:
            error_console.print(
                Text(f"Error fetching transitions: {e}", style="bold red"),
                highlight=True,
            )
            raise typer.Exit(1)

    display_transitions(transitions)

    if tailing:
        # Instead of reprinting the table repeatedly,
        # we launch the Textual TUI that uses a Log widget to display transitions.
        TransitionLogApp(
            client=client, execution_id=execution_id, initial_transitions=transitions
        ).run()
