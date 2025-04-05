import logging

from pydantic import ValidationError
from typing import Any
from ...common.protocol.models import task_to_spec
from ...autogen.openapi_model import (
    ChatSessionSystemDef,
    CreateAgentSystemDef,
    CreateAgentToolSystemDef,
    CreateDocSystemDef,
    CreateOwnerDocSystemDef,
    CreateSessionSystemDef,
    CreateTaskExecutionSystemDef,
    CreateTaskSystemDef,
    CreateUserSystemDef,
    DeleteAgentSystemDef,
    DeleteAgentToolSystemDef,
    DeleteDocSystemDef,
    DeleteSessionSystemDef,
    DeleteTaskSystemDef,
    DeleteUserSystemDef,
    EmbedDocSystemDef,
    GetAgentSystemDef,
    GetDocSystemDef,
    GetSessionHistorySystemDef,
    GetSessionSystemDef,
    GetTaskExecutionSystemDef,
    GetTaskSystemDef,
    GetUserSystemDef,
    HybridSearchOwnerDocsSystemDef,
    ListAgentsSystemDef,
    ListDocsSystemDef,
    ListSessionsSystemDef,
    ListTasksSystemDef,
    ListUsersSystemDef,
    PatchAgentSystemDef,
    PatchSessionSystemDef,
    PatchTaskSystemDef,
    PatchUserSystemDef,
    SimpleSearchDocsSystemDef,
    SystemDef,
    TextSearchOwnerDocsSystemDef,
    Tool,
    UpdateAgentSystemDef,
    UpdateAgentToolSystemDef,
    UpdateSessionSystemDef,
    UpdateTaskSystemDef,
    UpdateUserSystemDef,
    VectorSearchOwnerDocsSystemDef,

    CreateOwnerDocSystemDefArguments,
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
SYSTEM_ARGS_TYPES: dict[str] = {
    "CreateOwnerDocSystemDefArguments": CreateOwnerDocSystemDefArguments,
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
        print("*" * 100)
        print("FULL TOOL")
        print(tool)
        print("*" * 100)
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
                    print("*" * 100)
                    print("SYSTEM_DEF_TYPE")
                    print(system_def_type)
                    print("-" * 100)
                    print("SYSTEM DATA")
                    print(system_data)
                    print("-" * 100)
                    print("ORIGINAL TOOL.SYSTEM")
                    print(tool.system)
                    print("*" * 100)
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
            print("*" * 100)
            print("TOOL")
            print(tool)
            print("*" * 100)
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
