import logging
from typing import Any

from pydantic import ValidationError

from ...autogen.openapi_model import (
    ChatSessionSystemDef,
    ChatSessionSystemDefArguments,
    CreateAgentSystemDef,
    CreateAgentSystemDefArguments,
    CreateAgentToolSystemDef,
    CreateAgentToolSystemDefArguments,
    CreateDocSystemDef,
    CreateDocSystemDefArguments,
    CreateOwnerDocSystemDef,
    CreateOwnerDocSystemDefArguments,
    CreateSessionSystemDef,
    CreateSessionSystemDefArguments,
    CreateTaskExecutionSystemDef,
    CreateTaskExecutionSystemDefArguments,
    CreateTaskSystemDef,
    CreateTaskSystemDefArguments,
    CreateUserSystemDef,
    CreateUserSystemDefArguments,
    DeleteAgentSystemDef,
    DeleteAgentSystemDefArguments,
    DeleteAgentToolSystemDef,
    DeleteAgentToolSystemDefArguments,
    DeleteDocSystemDef,
    DeleteDocSystemDefArguments,
    DeleteSessionSystemDef,
    DeleteSessionSystemDefArguments,
    DeleteTaskSystemDef,
    DeleteTaskSystemDefArguments,
    DeleteUserSystemDef,
    DeleteUserSystemDefArguments,
    EmbedDocSystemDef,
    EmbedDocSystemDefArguments,
    GetAgentSystemDef,
    GetAgentSystemDefArguments,
    GetDocSystemDef,
    GetDocSystemDefArguments,
    GetSessionHistorySystemDef,
    GetSessionHistorySystemDefArguments,
    GetSessionSystemDef,
    GetSessionSystemDefArguments,
    GetTaskExecutionSystemDef,
    GetTaskExecutionSystemDefArguments,
    GetTaskSystemDef,
    GetTaskSystemDefArguments,
    GetUserSystemDef,
    GetUserSystemDefArguments,
    HybridSearchOwnerDocsSystemDef,
    HybridSearchOwnerDocsSystemDefArguments,
    ListAgentsSystemDef,
    ListAgentsSystemDefArguments,
    ListDocsSystemDef,
    ListDocsSystemDefArguments,
    ListSessionsSystemDef,
    ListSessionsSystemDefArguments,
    ListTasksSystemDef,
    ListTasksSystemDefArguments,
    ListUsersSystemDef,
    ListUsersSystemDefArguments,
    PatchAgentSystemDef,
    PatchAgentSystemDefArguments,
    PatchSessionSystemDef,
    PatchSessionSystemDefArguments,
    PatchTaskSystemDef,
    PatchTaskSystemDefArguments,
    PatchUserSystemDef,
    PatchUserSystemDefArguments,
    SimpleSearchDocsSystemDef,
    SimpleSearchDocsSystemDefArguments,
    SystemDef,
    TextSearchOwnerDocsSystemDef,
    TextSearchOwnerDocsSystemDefArguments,
    Tool,
    UpdateAgentSystemDef,
    UpdateAgentSystemDefArguments,
    UpdateAgentToolSystemDef,
    UpdateAgentToolSystemDefArguments,
    UpdateSessionSystemDef,
    UpdateSessionSystemDefArguments,
    UpdateTaskSystemDef,
    UpdateTaskSystemDefArguments,
    UpdateUserSystemDef,
    UpdateUserSystemDefArguments,
    VectorSearchOwnerDocsSystemDef,
    VectorSearchOwnerDocsSystemDefArguments,
)

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create a mapping of system_def_type strings to their corresponding classes
SYSTEM_DEF_TYPES: dict[str, type[SystemDef]] = {
    # Agent system definitions
    "CreateAgentSystemDef": CreateAgentSystemDef,
    "UpdateAgentSystemDef": UpdateAgentSystemDef,
    "PatchAgentSystemDef": PatchAgentSystemDef,
    "GetAgentSystemDef": GetAgentSystemDef,
    "ListAgentsSystemDef": ListAgentsSystemDef,
    "DeleteAgentSystemDef": DeleteAgentSystemDef,
    "CreateAgentToolSystemDef": CreateAgentToolSystemDef,
    "UpdateAgentToolSystemDef": UpdateAgentToolSystemDef,
    "DeleteAgentToolSystemDef": DeleteAgentToolSystemDef,
    # Document system definitions
    "CreateDocSystemDef": CreateDocSystemDef,
    "CreateOwnerDocSystemDef": CreateOwnerDocSystemDef,
    "EmbedDocSystemDef": EmbedDocSystemDef,
    "GetDocSystemDef": GetDocSystemDef,
    "ListDocsSystemDef": ListDocsSystemDef,
    "DeleteDocSystemDef": DeleteDocSystemDef,
    "SimpleSearchDocsSystemDef": SimpleSearchDocsSystemDef,
    "TextSearchOwnerDocsSystemDef": TextSearchOwnerDocsSystemDef,
    "VectorSearchOwnerDocsSystemDef": VectorSearchOwnerDocsSystemDef,
    "HybridSearchOwnerDocsSystemDef": HybridSearchOwnerDocsSystemDef,
    # Session system definitions
    "CreateSessionSystemDef": CreateSessionSystemDef,
    "UpdateSessionSystemDef": UpdateSessionSystemDef,
    "PatchSessionSystemDef": PatchSessionSystemDef,
    "GetSessionSystemDef": GetSessionSystemDef,
    "ListSessionsSystemDef": ListSessionsSystemDef,
    "DeleteSessionSystemDef": DeleteSessionSystemDef,
    "ChatSessionSystemDef": ChatSessionSystemDef,
    "GetSessionHistorySystemDef": GetSessionHistorySystemDef,
    # Task system definitions
    "CreateTaskSystemDef": CreateTaskSystemDef,
    "UpdateTaskSystemDef": UpdateTaskSystemDef,
    "PatchTaskSystemDef": PatchTaskSystemDef,
    "GetTaskSystemDef": GetTaskSystemDef,
    "ListTasksSystemDef": ListTasksSystemDef,
    "DeleteTaskSystemDef": DeleteTaskSystemDef,
    "CreateTaskExecutionSystemDef": CreateTaskExecutionSystemDef,
    "GetTaskExecutionSystemDef": GetTaskExecutionSystemDef,
    # User system definitions
    "CreateUserSystemDef": CreateUserSystemDef,
    "UpdateUserSystemDef": UpdateUserSystemDef,
    "PatchUserSystemDef": PatchUserSystemDef,
    "GetUserSystemDef": GetUserSystemDef,
    "ListUsersSystemDef": ListUsersSystemDef,
    "DeleteUserSystemDef": DeleteUserSystemDef,
}
SYSTEM_ARGS_TYPES: dict[str, type[Any]] = {
    # Agent system arguments
    "CreateAgentSystemDefArguments": CreateAgentSystemDefArguments,
    "UpdateAgentSystemDefArguments": UpdateAgentSystemDefArguments,
    "PatchAgentSystemDefArguments": PatchAgentSystemDefArguments,
    "GetAgentSystemDefArguments": GetAgentSystemDefArguments,
    "ListAgentsSystemDefArguments": ListAgentsSystemDefArguments,
    "DeleteAgentSystemDefArguments": DeleteAgentSystemDefArguments,
    "CreateAgentToolSystemDefArguments": CreateAgentToolSystemDefArguments,
    "UpdateAgentToolSystemDefArguments": UpdateAgentToolSystemDefArguments,
    "DeleteAgentToolSystemDefArguments": DeleteAgentToolSystemDefArguments,
    # Document system arguments
    "CreateDocSystemDefArguments": CreateDocSystemDefArguments,
    "CreateOwnerDocSystemDefArguments": CreateOwnerDocSystemDefArguments,
    "DeleteDocSystemDefArguments": DeleteDocSystemDefArguments,
    "EmbedDocSystemDefArguments": EmbedDocSystemDefArguments,
    "GetDocSystemDefArguments": GetDocSystemDefArguments,
    "ListDocsSystemDefArguments": ListDocsSystemDefArguments,
    "SimpleSearchDocsSystemDefArguments": SimpleSearchDocsSystemDefArguments,
    "TextSearchOwnerDocsSystemDefArguments": TextSearchOwnerDocsSystemDefArguments,
    "VectorSearchOwnerDocsSystemDefArguments": VectorSearchOwnerDocsSystemDefArguments,
    "HybridSearchOwnerDocsSystemDefArguments": HybridSearchOwnerDocsSystemDefArguments,
    # Session system arguments
    "CreateSessionSystemDefArguments": CreateSessionSystemDefArguments,
    "UpdateSessionSystemDefArguments": UpdateSessionSystemDefArguments,
    "PatchSessionSystemDefArguments": PatchSessionSystemDefArguments,
    "GetSessionSystemDefArguments": GetSessionSystemDefArguments,
    "ListSessionsSystemDefArguments": ListSessionsSystemDefArguments,
    "DeleteSessionSystemDefArguments": DeleteSessionSystemDefArguments,
    "ChatSessionSystemDefArguments": ChatSessionSystemDefArguments,
    "GetSessionHistorySystemDefArguments": GetSessionHistorySystemDefArguments,
    # Task system arguments
    "CreateTaskSystemDefArguments": CreateTaskSystemDefArguments,
    "UpdateTaskSystemDefArguments": UpdateTaskSystemDefArguments,
    "PatchTaskSystemDefArguments": PatchTaskSystemDefArguments,
    "GetTaskSystemDefArguments": GetTaskSystemDefArguments,
    "ListTasksSystemDefArguments": ListTasksSystemDefArguments,
    "DeleteTaskSystemDefArguments": DeleteTaskSystemDefArguments,
    "CreateTaskExecutionSystemDefArguments": CreateTaskExecutionSystemDefArguments,
    "GetTaskExecutionSystemDefArguments": GetTaskExecutionSystemDefArguments,
    # User system arguments
    "CreateUserSystemDefArguments": CreateUserSystemDefArguments,
    "UpdateUserSystemDefArguments": UpdateUserSystemDefArguments,
    "PatchUserSystemDefArguments": PatchUserSystemDefArguments,
    "GetUserSystemDefArguments": GetUserSystemDefArguments,
    "ListUsersSystemDefArguments": ListUsersSystemDefArguments,
    "DeleteUserSystemDefArguments": DeleteUserSystemDefArguments,
}


def system_tool_type_cast(tools: list[Tool]) -> list[Tool]:
    """
    Casts system tools to their specific SystemDef subclass types.

    This function examines each tool in the provided list and, if it's a system tool,
    converts its system property from the base SystemDef type to the appropriate
    subclass based on the system_def_type value.

    Args:
        tools: A list of Tool objects to process

    Returns:
        The same list of tools with system tools properly cast to their specific types

    Raises:
        ValueError: If a system tool has an unknown system_def_type or validation fails
    """
    for tool in tools:
        if tool.type == "system" and tool.system is not None:
            try:
                # Get the system_def_type value to determine the correct type
                system_def_type = tool.system.system_def_type
                logger.debug(f"Processing system tool with type: {system_def_type}")

                # Look up the class in our mapping
                if system_def_type in SYSTEM_DEF_TYPES:
                    target_class = SYSTEM_DEF_TYPES[system_def_type]

                    # Get the data from the original object
                    system_data = tool.system.model_dump(mode="json")
                    # Create a new instance of the target class with the data
                    try:
                        tool.system = target_class.model_validate(system_data)
                    except ValidationError as e:
                        logger.error(
                            f"Failed to validate system data as {target_class.__name__}: {e}"
                        )
                        msg = f"Failed to validate system data as {target_class.__name__}: {e}"
                        raise ValueError(msg)
                else:
                    logger.error(f"Unknown system_def_type: {system_def_type}")
                    msg = (
                        f"Unknown system_def_type: {system_def_type}. "
                        f"Valid types are: {', '.join(SYSTEM_DEF_TYPES.keys())}"
                    )
                    raise ValueError(msg)
            except Exception as e:
                logger.exception(f"Error processing system tool: {e}")
                raise

    return tools


def system_args_type_cast(steps: list[Any], tools: list[Tool]) -> list[Any]:
    for step in steps:
        step_type = getattr(step, "kind_")
        if step_type == "tool_call":
            arguments = getattr(step, "arguments", {})
            tool_name = getattr(step, "tool")
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool is not None and tool.type == "system" and tool.system is not None:
                system_args_type = tool.system.system_def_type + "Arguments"
                if system_args_type in SYSTEM_ARGS_TYPES:
                    arguments = SYSTEM_ARGS_TYPES[system_args_type].model_validate(arguments)
                else:
                    logger.error(f"Unknown system_def_type: {system_args_type}")
                    msg = (
                        f"Unknown system_def_type: {system_args_type}. "
                        f"Valid types are: {', '.join(SYSTEM_DEF_TYPES.keys())}"
                    )
                    raise ValueError(msg)
    return steps
