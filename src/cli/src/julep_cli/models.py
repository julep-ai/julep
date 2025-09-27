from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool


class CreateAgentRequest(BaseModel):
    """
    Payload for creating an agent
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    metadata: dict[str, Any] | None = None
    name: Annotated[str, Field(max_length=255, min_length=1)]
    """
    Name of the agent
    """
    canonical_name: Annotated[
        str | None,
        Field(max_length=255, min_length=1, pattern="^[a-zA-Z][a-zA-Z0-9_]*$"),
    ] = None
    """
    Canonical name of the agent
    """
    about: str = ""
    """
    About the agent
    """
    model: str = ""
    """
    Model name to use (gpt-4-turbo, gemini-nano etc)
    """
    instructions: str | list[str] = []
    """
    Instructions for the agent
    """
    default_settings: Any | None = None
    """
    Default settings for all sessions created by this agent
    """


class CreateToolRequest(BaseModel):
    """
    Payload for creating a tool
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    name: Annotated[str, Field(max_length=40, pattern="^[^\\W0-9]\\w*$")]
    """
    Name of the tool (must be unique for this agent and a valid python identifier string )
    """
    type: Literal[
        "function",
        "integration",
        "system",
        "api_call",
        "computer_20241022",
        "text_editor_20241022",
        "bash_20241022",
    ]
    """
    Type of the tool
    """
    description: str | None = None
    """
    Description of the tool
    """
    function: Any | None = None  # TODO: Change to FunctionDef
    """
    The function to call
    """
    integration: (  # TODO: Change to available integrations
        Any | None
    ) = None
    """
    The integration to call
    """
    system: Any | None = None  # TODO: Change to SystemDef
    """
    The system to call
    """
    api_call: Any | None = None  # TODO: Change to ApiCallDef
    """
    The API call to make
    """
    computer_20241022: Any | None = None  # TODO: Change to Computer20241022Def
    """
    (Alpha) Anthropic new tools
    """
    text_editor_20241022: Any | None = None  # TODO: Change to TextEditor20241022Def
    bash_20241022: Any | None = None  # TODO: Change to Bash20241022Def


class CreateTaskRequest(BaseModel):
    """
    Payload for creating a task
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    name: Annotated[str, Field(max_length=255, min_length=1)]
    """
    The name of the task.
    """
    canonical_name: Annotated[
        str | None,
        Field(max_length=255, min_length=1, pattern="^[a-zA-Z][a-zA-Z0-9_]*$"),
    ] = None
    """
    The canonical name of the task.
    """
    description: str = ""
    """
    The description of the task.
    """
    main: Annotated[
        list[
            Any  # TODO: Change to Task steps
        ],
        Field(min_length=1),
    ]
    """
    The entrypoint of the task.
    """
    input_schema: dict[str, Any] | None = None
    """
    The schema for the input to the task. `null` means all inputs are valid.
    """
    tools: list[CreateToolRequest] = []  # TODO: Change to TaskTool
    """
    Tools defined specifically for this task not included in the Agent itself.
    """
    inherit_tools: StrictBool = False
    """
    Whether to inherit tools from the parent agent or not. Defaults to false.
    """
    metadata: dict[str, Any] | None = None


class LockedEntity(BaseModel):
    """
    A locked entity is information about an entity (agent | task | tool) that has been created on the Julep platform
    """

    path: str
    """
    The path to the yaml file that defines the entity
    """
    id: str
    """
    The ID of the entity
    """
    last_synced: str
    """
    The last time the entity was synced with the remote Julep platform
    """
    revision_hash: str
    """
    The revision hash of the entity (sha256 of the yaml file contents)
    """


class TaskAgentRelationship(BaseModel):
    id: str
    """
    The ID of the task
    """
    agent_id: str
    """
    The ID of the agent
    """


class ToolAgentRelationship(BaseModel):
    id: str
    """
    The ID of the tool
    """
    agent_id: str
    """
    The ID of the agent
    """


class Relationships(BaseModel):
    """
    The relationships between agents, tasks, and tools
    """

    tasks: list[TaskAgentRelationship] = []
    """
    The tasks that have been created on the Julep platform
    """
    tools: list[ToolAgentRelationship] = []
    """
    The tools that have been created on the Julep platform
    """


class LockFileContents(BaseModel):
    """
    Schema for the julep-lock.json file
    """

    lockfile_version: str = "0.1.0"
    """
    The version of the lock file
    """
    agents: list[LockedEntity] = []
    """
    The agents that have been created on the Julep platform
    """
    tasks: list[LockedEntity] = []
    """
    The tasks that have been created on the Julep platform
    """
    tools: list[LockedEntity] = []
    """
    The tools that have been created on the Julep platform
    """
    relationships: Relationships | None = None
    """
    The relationships between agents, tasks, and tools
    """
