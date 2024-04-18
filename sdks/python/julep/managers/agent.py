import json
from typing import Optional, TypedDict
from uuid import UUID

from beartype import beartype
from beartype.typing import Any, Awaitable, Dict, List, Literal, Union

from ..api.types import (
    Agent,
    AgentDefaultSettings,
    CreateDoc,
    CreateToolRequest,
    ResourceCreatedResponse,
    ListAgentsResponse,
    ResourceUpdatedResponse,
)

from .utils import rewrap_in_class

from .base import BaseManager
from .utils import is_valid_uuid4, NotSet
from .types import (
    ToolDict,
    FunctionDefDict,
    DefaultSettingsDict,
    DocDict,
)


###########
## TYPES ##
###########


ModelName = Literal[
    "julep-ai/samantha-1",
    "julep-ai/samantha-1-turbo",
]


class AgentCreateArgs(TypedDict):
    name: str
    about: Optional[str]
    instructions: Optional[List[str]]
    tools: List[ToolDict] = []
    functions: List[FunctionDefDict] = []
    default_settings: DefaultSettingsDict = {}
    model: ModelName = "julep-ai/samantha-1-turbo"
    docs: List[DocDict] = []
    metadata: Dict[str, Any] = {}


class AgentUpdateArgs(TypedDict):
    about: Optional[str] = None
    instructions: Optional[List[str]] = None
    name: Optional[str] = None
    model: Optional[str] = None
    default_settings: Optional[DefaultSettingsDict] = None
    metadata: Optional[Dict[str, Any]] = None
    overwrite: bool = False


class BaseAgentsManager(BaseManager):
    """
    A class responsible for managing agent entities.

    This manager handles CRUD operations for agents including retrieving, creating, listing, deleting, and updating agents using an API client.

    Attributes:
        api_client (ApiClientType): The client responsible for API interactions.

    Methods:
        _get(self, id: Union[str, UUID]) -> Union[Agent, Awaitable[Agent]]:
            Retrieves a single agent by its UUID.
            Args:
                id (Union[str, UUID]): The UUID of the agent to retrieve.
            Returns:
                The agent object or an awaitable that resolves to the agent object.

        _create(self, name: str, about: str, instructions: List[str], tools: List[ToolDict] = [], functions: List[FunctionDefDict] = [], default_settings: DefaultSettingsDict = {}, model: ModelName = 'julep-ai/samantha-1-turbo', docs: List[DocDict] = [], metadata: Dict[str, Any] = {}) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
            Creates an agent with the given specifications.
            Args:
                name (str): The name of the new agent.
                about (str): Description about the new agent.
                instructions (List[str]): List of instructions or instruction dictionaries for the new agent.
                tools (List[ToolDict], optional): List of tool dictionaries. Defaults to an empty list.
                functions (List[FunctionDefDict], optional): List of function definition dictionaries. Defaults to an empty list.
                default_settings (DefaultSettingsDict, optional): Dictionary of default settings for the new agent. Defaults to an empty dictionary.
                model (ModelName, optional): The model name for the new agent. Defaults to 'julep-ai/samantha-1-turbo'.
                docs (List[DocDict], optional): List of document dictionaries for the new agent. Defaults to an empty list.
                metadata (Dict[str, Any], optional): Dictionary of metadata for the new agent. Defaults to an empty dictionary.
            Returns:
                The response indicating creation or an awaitable that resolves to the creation response.

        _list_items(self, limit: Optional[int] = None, offset: Optional[int] = None, metadata_filter: Dict[str, Any] = {}) -> Union[ListAgentsResponse, Awaitable[ListAgentsResponse]]:
            Lists agents with pagination support and optional metadata filtering.
            Args:
                limit (Optional[int], optional): The maximum number of agents to list. Defaults to None.
                offset (Optional[int], optional): The number of agents to skip (for pagination). Defaults to None.
                metadata_filter (Dict[str, Any], optional): Filters for querying agents based on metadata. Defaults to an empty dictionary.
            Returns:
                The list of agents or an awaitable that resolves to the list of agents.

        _delete(self, agent_id: Union[str, UUID]) -> Union[None, Awaitable[None]]:
            Deletes an agent with the specified UUID.
            Args:
                agent_id (Union[str, UUID]): The UUID of the agent to delete.
            Returns:
                None or an awaitable that resolves to None.

        _update(self, agent_id: Union[str, UUID], about: Optional[str] = None, instructions: Optional[List[str]] = None, name: Optional[str] = None, model: Optional[str] = None, default_settings: Optional[DefaultSettingsDict] = None, metadata: Dict[str, Any] = {}) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]:
            Updates the specified fields of an agent.
            Args:
                agent_id (Union[str, UUID]): The UUID of the agent to update.
                about (Optional[str], optional): The new description about the agent.
                instructions (Optional[List[str]], optional): The new list of instructions or instruction dictionaries.
                name (Optional[str], optional): The new name for the agent.
                model (Optional[str], optional): The new model name for the agent.
                default_settings (Optional[DefaultSettingsDict], optional): The new default settings dictionary for the agent.
                metadata (Dict[str, Any])
            Returns:
                The response indicating successful update or an awaitable that resolves to the update response.
    """

    def _get(self, id: Union[str, UUID]) -> Union[Agent, Awaitable[Agent]]:
        """
        Retrieves an agent based on the provided identifier.

        Args:
            id (Union[str, UUID]): The identifier of the agent, which can be a string or UUID object.

        Returns:
            Union[Agent, Awaitable[Agent]]: The agent object or an awaitable yielding the agent object, depending on the API client.

        Raises:
            AssertionError: If the provided id is not a valid UUID v4.
        """
        assert is_valid_uuid4(id), "id must be a valid UUID v4"
        return self.api_client.get_agent(agent_id=id)

    def _create(
        self,
        name: str,
        about: str = "",
        instructions: List[str] = [],
        tools: List[ToolDict] = [],
        functions: List[FunctionDefDict] = [],
        default_settings: DefaultSettingsDict = {},
        model: ModelName = "julep-ai/samantha-1-turbo",
        docs: List[DocDict] = [],
        metadata: Dict[str, Any] = {},
    ) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
        # Instructions are expected to be provided in the correct format
        """
        Create a new agent with the specified configuration.

        Args:
            name (str): Name of the agent.
            about (str): Information about the agent.
            instructions (List[str]): List of instructions as either string or dictionaries for the agent.
            tools (List[ToolDict], optional): List of tool configurations for the agent. Defaults to an empty list.
            functions (List[FunctionDefDict], optional): List of function definitions for the agent. Defaults to an empty list.
            default_settings (DefaultSettingsDict, optional): Dictionary of default settings for the agent. Defaults to an empty dict.
            model (ModelName, optional): The model name identifier. Defaults to 'julep-ai/samantha-1-turbo'.
            docs (List[DocDict], optional): List of document configurations for the agent. Defaults to an empty list.
            metadata (Dict[str, Any])

        Returns:
            Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]: The response object indicating the resource has been created or a future of the response object if the creation is being awaited.

        Raises:
            AssertionError: If both functions and tools are provided.

        Notes:
            The `_create` method is meant to be used internally and should be considered private.
            It assumes the input data for instructions, tools, and docs will have the proper format,
            and items in the 'instructions' list will be converted to Instruction instances.
        """
        # Ensure that only functions or tools are provided
        assert not (functions and tools), "Only functions or tools can be provided"

        # Cast functions/tools to a list of CreateToolRequest objects
        tools: List[CreateToolRequest] = (
            [
                CreateToolRequest(type="function", function=function)
                for function in functions
            ]
            if functions
            else [CreateToolRequest(**tool) for tool in tools]
        )

        # Cast default_settings to AgentDefaultSettings
        default_settings: AgentDefaultSettings = AgentDefaultSettings(
            **default_settings
        )

        # Cast docs to a list of CreateDoc objects
        docs: List[CreateDoc] = [CreateDoc(**doc) for doc in docs]

        return self.api_client.create_agent(
            name=name,
            about=about,
            instructions=instructions,
            tools=tools,
            default_settings=default_settings,
            model=model,
            docs=docs,
            metadata=metadata,
        )

    def _list_items(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        metadata_filter: str = "{}",
    ) -> Union[ListAgentsResponse, Awaitable[ListAgentsResponse]]:
        """
        Lists items with optional pagination.

            This method wraps the `list_agents` API call and includes optional limit and offset parameters for pagination.

            Args:
                limit (Optional[int], optional): The maximum number of items to return. Defaults to None, which means no limit.
                offset (Optional[int], optional): The index of the first item to return. Defaults to None, which means no offset.

            Returns:
                Union[ListAgentsResponse, Awaitable[ListAgentsResponse]]: A ListAgentsResponse object, or an awaitable that resolves to a ListAgentsResponse object.
        """
        return self.api_client.list_agents(
            limit=limit,
            offset=offset,
            metadata_filter=metadata_filter,
        )

    def _delete(self, agent_id: Union[str, UUID]) -> Union[None, Awaitable[None]]:
        """
        Delete an agent by its ID.

        Args:
            agent_id (Union[str, UUID]): The UUID v4 of the agent to be deleted.

        Returns:
            Union[None, Awaitable[None]]: A future that resolves to None if the
            operation is asynchronous, or None immediately if the operation is
            synchronous.

        Raises:
            AssertionError: If `agent_id` is not a valid UUID v4.
        """
        assert is_valid_uuid4(agent_id), "id must be a valid UUID v4"
        return self.api_client.delete_agent(agent_id=agent_id)

    def _update(
        self,
        agent_id: Union[str, UUID],
        about: Optional[str] = NotSet,
        instructions: List[str] = NotSet,
        name: Optional[str] = NotSet,
        model: Optional[str] = NotSet,
        default_settings: Optional[DefaultSettingsDict] = NotSet,
        metadata: Dict[str, Any] = NotSet,
        overwrite: bool = False,
    ) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]:
        """
        Update the agent's properties.

            Args:
                agent_id (Union[str, UUID]): The unique identifier for the agent, which can be a string or UUID object.
                about (Optional[str], optional): A brief description of the agent. Defaults to None.
                instructions (Optional[List[str]], optional): A list of either strings or instruction dictionaries that will be converted into Instruction objects. Defaults to None.
                name (Optional[str], optional): The name of the agent. Defaults to None.
                model (Optional[str], optional): The model identifier for the agent. Defaults to None.
                default_settings (Optional[DefaultSettingsDict], optional): A dictionary of default settings to apply to the agent. Defaults to None.
                metadata (Dict[str, Any])
                overwrite (bool, optional): Whether to overwrite the existing agent settings. Defaults to False.

            Returns:
                Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]: An object representing the response for the resource updated, which can also be an awaitable in asynchronous contexts.

            Raises:
                AssertionError: If the provided agent_id is not validated by the is_valid_uuid4 function.

            Note:
                This method asserts that the agent_id must be a valid UUID v4. The instructions and default_settings, if provided, are converted into their respective object types before making the update API call.
        """
        assert is_valid_uuid4(agent_id), "id must be a valid UUID v4"

        if default_settings is not NotSet:
            default_settings: AgentDefaultSettings = AgentDefaultSettings(
                **default_settings
            )

        updateFn = (
            self.api_client.update_agent if overwrite else self.api_client.patch_agent
        )

        update_payload = dict(
            agent_id=agent_id,
            about=about,
            instructions=instructions,
            name=name,
            model=model,
            default_settings=default_settings,
            metadata=metadata,
        )

        update_payload = {k: v for k, v in update_payload.items() if v is not NotSet}

        return updateFn(**update_payload)


class AgentsManager(BaseAgentsManager):
    """
    A class for managing agents, inheriting from `BaseAgentsManager`.

    This class provides functionalities to interact with and manage agents, including creating, retrieving, listing, updating, and deleting agents. It utilizes type annotations to ensure type correctness at runtime using the `beartype` decorator.

    Methods:
        get(id: Union[str, UUID]) -> Agent:
            Retrieves an agent by its unique identifier.

            Args:
                id (Union[str, UUID]): The unique identifier of the agent, which can be either a string or a UUID.

            Returns:
                Agent: The agent with the corresponding identifier.

        create(*, name: str, about: str, instructions: List[str], tools: List[ToolDict]=[], functions: List[FunctionDefDict]=[], default_settings: DefaultSettingsDict={}, model: ModelName='julep-ai/samantha-1-turbo', docs: List[DocDict]=[]) -> ResourceCreatedResponse:
            Creates a new agent with the provided details.

            Args:
                name (str): The name of the agent.
                about (str): A description of the agent.
                instructions (List[str]): A list of instructions or dictionaries defining instructions.
                tools (List[ToolDict], optional): A list of dictionaries defining tools. Defaults to an empty list.
                functions (List[FunctionDefDict], optional): A list of dictionaries defining functions. Defaults to an empty list.
                default_settings (DefaultSettingsDict, optional): A dictionary of default settings. Defaults to an empty dictionary.
                model (ModelName, optional): The model name to be used. Defaults to 'julep-ai/samantha-1-turbo'.
                docs (List[DocDict], optional): A list of dictionaries defining documentation. Defaults to an empty list.
                metadata (Dict[str, Any])

            Returns:
                ResourceCreatedResponse: The response indicating the resource (agent) was successfully created.

        list(*, limit: Optional[int]=None, offset: Optional[int]=None) -> List[Agent]:
            Lists all agents with pagination support.

            Args:
                limit (Optional[int], optional): The maximum number of agents to retrieve. Defaults to None, meaning no limit.
                offset (Optional[int], optional): The number of agents to skip (for pagination). Defaults to None.

            Returns:
                List[Agent]: A list of agents, considering the pagination parameters.

        delete(agent_id: Union[str, UUID]):
            Deletes an agent by its unique identifier.

            Args:
                agent_id (Union[str, UUID]): The unique identifier of the agent to be deleted.

        update(*, agent_id: Union[str, UUID], about: Optional[str]=None, instructions: Optional[List[str]]=None, name: Optional[str]=None, model: Optional[str]=None, default_settings: Optional[DefaultSettingsDict]=None) -> ResourceUpdatedResponse:
            Updates an existing agent with new details.

            Args:
                agent_id (Union[str, UUID]): The unique identifier of the agent to be updated.
                about (Optional[str], optional): A new description of the agent. Defaults to None (no change).
                instructions (Optional[List[str]], optional): A new list of instructions or dictionaries defining instructions. Defaults to None (no change).
                name (Optional[str], optional): A new name for the agent. Defaults to None (no change).
                model (Optional[str], optional): A new model name to be used. Defaults to None (no change).
                default_settings (Optional[DefaultSettingsDict], optional): A new dictionary of default settings. Defaults to None (no change).
                metadata (Dict[str, Any])

            Returns:
                ResourceUpdatedResponse: The response indicating the resource (agent) was successfully updated.
    """

    @beartype
    def get(self, id: Union[str, UUID]) -> Agent:
        """
        Retrieve an Agent object by its identifier.

        Args:
            id (Union[str, UUID]): The unique identifier of the Agent to be retrieved.

        Returns:
            Agent: An instance of the Agent with the specified ID.

        Raises:
            BeartypeException: If the type of `id` is neither a string nor a UUID.
            Any exception raised by the `_get` method.
        """
        return self._get(id=id)

    @beartype
    @rewrap_in_class(Agent)
    def create(self, **kwargs: AgentCreateArgs) -> Agent:
        """
        Creates a new resource with the specified details.

        Args:
            name (str): The name of the resource.
            about (str): A description of the resource.
            instructions (List[str]): A list of instructions or dictionaries with instruction details.
            tools (List[ToolDict], optional): A list of dictionaries with tool details. Defaults to an empty list.
            functions (List[FunctionDefDict], optional): A list of dictionaries with function definition details. Defaults to an empty list.
            default_settings (DefaultSettingsDict, optional): A dictionary with default settings. Defaults to an empty dictionary.
            model (ModelName, optional): The name of the model to use. Defaults to 'julep-ai/samantha-1-turbo'.
            docs (List[DocDict], optional): A list of dictionaries with documentation details. Defaults to an empty list.
            metadata (Dict[str, Any])

        Returns:
            Agent: An instance of the Agent with the specified details

        Note:
            This function is decorated with `@beartype`, which will perform runtime type checking on the arguments.
        """
        result = self._create(**kwargs)
        return result

    @beartype
    def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        metadata_filter: Dict[str, Any] = {},
    ) -> List[Agent]:
        """
        List the Agent objects, possibly with pagination.

        Args:
          limit (Optional[int], optional): The maximum number of Agent objects to return.
                                           Defaults to None, meaning no limit is applied.
          offset (Optional[int], optional): The number of initial Agent objects to skip before
                                            starting to collect the return list. Defaults to None,
                                            meaning no offset is applied.

        Returns:
          List[Agent]: A list of Agent objects.

        Raises:
          BeartypeDecorHintPepParamViolation: If the function is called with incorrect types
                                              for the `limit` or `offset` parameters.
        """
        metadata_filter_string = json.dumps(metadata_filter)

        return self._list_items(
            limit=limit,
            offset=offset,
            metadata_filter=metadata_filter_string,
        ).items

    @beartype
    def delete(self, agent_id: Union[str, UUID]):
        """
        Delete the agent with the specified ID.

            Args:
                agent_id (Union[str, UUID]): The identifier of the agent to be deleted.

            Returns:
                The return type depends on the implementation of the `_delete` method. This will typically be `None`
                if the deletion is successful, or an error may be raised if the deletion fails.

            Note:
                The `@beartype` decorator is used to enforce type checking of the `agent_id` parameter.
        """
        return self._delete(agent_id=agent_id)

    @beartype
    @rewrap_in_class(Agent)
    def update(self, *, agent_id: Union[str, UUID], **kwargs: AgentUpdateArgs) -> Agent:
        """
        Update the properties of a resource.

        This function updates various attributes of an existing resource based on the provided keyword arguments. All updates are optional and are applied only if the corresponding argument is given.

        Args:
            agent_id (Union[str, UUID]): The identifier of the agent, either as a string or a UUID object.
            about (Optional[str], optional): A brief description of the agent. Defaults to None.
            instructions (Optional[List[str]], optional): A list of instructions or instruction dictionaries to update the agent with. Defaults to None.
            name (Optional[str], optional): The new name to assign to the agent. Defaults to None.
            model (Optional[str], optional): The model identifier to associate with the agent. Defaults to None.
            default_settings (Optional[DefaultSettingsDict], optional): A dictionary of default settings to apply to the agent. Defaults to None.
            metadata (Dict[str, Any])
            overwrite (bool, optional): Whether to overwrite the existing agent settings. Defaults to False.

        Returns:
            ResourceUpdatedResponse: An object representing the response to the update request.

        Note:
            This method is decorated with `beartype`, which means it enforces type annotations at runtime.
        """

        result = self._update(agent_id=agent_id, **kwargs)
        return result


class AsyncAgentsManager(BaseAgentsManager):
    """
    A class for managing asynchronous agent operations.

    This class provides asynchronous methods for creating, retrieving, updating,
    listing, and deleting agents. It is a subclass of BaseAgentsManager, which
    defines the underlying functionality and structure that this class utilizes.

    Attributes:
        None explicitly listed, as they are inherited from the `BaseAgentsManager` class.

    Methods:
        get:
            Retrieves a single agent by its ID.

            Args:
                id (Union[UUID, str]): The unique identifier of the agent to retrieve.

            Returns:
                Agent: The requested agent.

        create:
            Creates a new agent with the provided specifications.

            Args:
                name (str): The name of the agent to create.
                about (str): A description of the agent.
                instructions (List[str]): The instructions for operating the agent.
                tools (List[ToolDict], optional): An optional list of tools for the agent.
                functions (List[FunctionDefDict], optional): An optional list of functions the agent can perform.
                default_settings (DefaultSettingsDict, optional): Optional default settings for the agent.
                model (ModelName, optional): The model name to associate with the agent, defaults to 'julep-ai/samantha-1-turbo'.
                docs (List[DocDict], optional): An optional list of documents associated with the agent.
                metadata (Dict[str, Any])

            Returns:
                ResourceCreatedResponse: A response indicating the agent was created successfully.

        list:
            Asynchronously lists agents with optional pagination and returns an awaitable object.

            Args:
                limit (Optional[int], optional): The maximum number of agents to retrieve.
                offset (Optional[int], optional): The number of agents to skip before starting to collect the results.

            Returns:
                List[Agent]: A list of agents.

        delete:
            Asynchronously deletes an agent by its ID and returns an awaitable object.

            Args:
                agent_id (Union[str, UUID]): The unique identifier of the agent to delete.

            Returns:
                The response from the delete operation (specific return type may vary).

        update:
            Asynchronously updates the specified fields of an agent by its ID and returns an awaitable object.

            Args:
                agent_id (Union[str, UUID]): The unique identifier of the agent to update.
                about (Optional[str], optional): An optional new description for the agent.
                instructions (Optional[List[str]], optional): Optional new instructions for the agent.
                name (Optional[str], optional): An optional new name for the agent.
                model (Optional[str], optional): Optional new model associated with the agent.
                default_settings (Optional[DefaultSettingsDict], optional): Optional new default settings for the agent.
                metadata (Dict[str, Any])

            Returns:
                ResourceUpdatedResponse: A response indicating the agent was updated successfully.
    """

    @beartype
    async def get(self, id: Union[UUID, str]) -> Agent:
        """
        Asynchronously retrieve an Agent object by its ID.

        The `id` parameter can be either a UUID or a string representation of a UUID.

        Args:
            id (Union[UUID, str]): The unique identifier of the Agent to retrieve.

        Returns:
            Agent: The Agent object associated with the given id.

        Raises:
            Beartype exceptions: If the input id does not conform to the specified types.
            Other exceptions: Depending on the implementation of the `_get` method.
        """
        return await self._get(id=id)

    @beartype
    @rewrap_in_class(Agent)
    async def create(self, **kwargs: AgentCreateArgs) -> Agent:
        """
        Create a new resource asynchronously with specified details.

        This function is decorated with `beartype` to ensure that arguments conform to specified types.

        Args:
            name (str): The name of the resource to create.
            about (str): Information or description about the resource.
            instructions (List[str]): A list of strings or dictionaries detailing the instructions for the resource.
            tools (List[ToolDict], optional): A list of dictionaries representing the tools associated with the resource. Defaults to an empty list.
            functions (List[FunctionDefDict], optional): A list of dictionaries defining functions that can be performed with the resource. Defaults to an empty list.
            default_settings (DefaultSettingsDict, optional): A dictionary with default settings for the resource. Defaults to an empty dictionary.
            model (ModelName, optional): The model identifier to use for the resource. Defaults to 'julep-ai/samantha-1-turbo'.
            docs (List[DocDict], optional): A list of dictionaries containing documentation for the resource. Defaults to an empty list.
            metadata (Dict[str, Any])

        Returns:
            Agent: An instance of the Agent with the specified details

        Raises:
            The exceptions that may be raised are not specified in the signature and depend on the implementation of the _create method.
        """
        result = await self._create(**kwargs)
        return result

    @beartype
    async def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        metadata_filter: Dict[str, Any] = {},
    ) -> List[Agent]:
        """
        Asynchronously lists agents with optional limit and offset.

        This method wraps the call to a private method '_list_items' which performs the actual listing
        of agent items. It uses the 'beartype' decorator for runtime type checking.

        Args:
            limit (Optional[int], optional): The maximum number of agent items to return. Defaults to None, which means no limit.
            offset (Optional[int], optional): The offset from where to start the listing. Defaults to None, which means start from the beginning.

        Returns:
            List[Agent]: A list of agent items collected based on the provided 'limit' and 'offset' parameters.
        """
        metadata_filter_string = json.dumps(metadata_filter)

        return (
            await self._list_items(
                limit=limit,
                offset=offset,
                metadata_filter=metadata_filter_string,
            )
        ).items

    @beartype
    async def delete(self, agent_id: Union[str, UUID]):
        """
        Asynchronously deletes an agent given its identifier.

        This function is decorated with @beartype to ensure type checking of the input argument at runtime.

        Args:
            agent_id (Union[str, UUID]): The identifier of the agent to be deleted. Can be a string or a UUID object.

        Returns:
            The result of the asynchronous deletion operation, which is implementation-dependent.
        """
        return await self._delete(agent_id=agent_id)

    @beartype
    @rewrap_in_class(Agent)
    async def update(
        self, *, agent_id: Union[str, UUID], **kwargs: AgentUpdateArgs
    ) -> Agent:
        """
        Asynchronously update an agent's details.

        This function is decorated with `beartype` to enforce the type checking of parameters. It updates the properties of the agent identified by `agent_id`.

        Args:
            agent_id (Union[str, UUID]): Unique identifier for the agent. It can be a string or a UUID object.
            about (Optional[str]): Additional information about the agent. Default is None.
            instructions (Optional[List[str]]): A list of instructions or instruction dictionaries. Default is None.
            name (Optional[str]): The name of the agent. Default is None.
            model (Optional[str]): The model identifier or name. Default is None.
            default_settings (Optional[DefaultSettingsDict]): Dictionary with default settings for the agent. Default is None.
            metadata (Dict[str, Any])
            overwrite (bool): Whether to overwrite the existing agent settings. Default is False.

        Returns:
            ResourceUpdatedResponse: An object containing the details of the update response.
        """
        result = await self._update(agent_id=agent_id, **kwargs)
        return result
