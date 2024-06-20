from typing import Union, Awaitable, Optional, List, Dict, Any, TypedDict, cast
from uuid import UUID
from beartype import beartype
from .base import BaseManager
from .utils import is_valid_uuid4
from ..api.types import (
    ResourceCreatedResponse,
    WorkflowStep,
    Task,
    Execution,
    ExecutionStatus,
)
from .utils import rewrap_in_class


class TaskCreateArgs(TypedDict):
    agent_id: Union[UUID, str]
    name: str
    description: Optional[str]
    tools_available: Optional[List[str]]
    input_schema: Optional[Dict[str, Any]]
    main: List[WorkflowStep]


class StartTaskExecutionArgs(TypedDict):
    agent_id: Union[UUID, str]
    task_id: Union[UUID, str]
    arguments: Dict[str, Any]
    status: ExecutionStatus


class BaseTasksManager(BaseManager):
    """
    A class responsible for managing task entities.

    This manager handles CRUD operations for tasks including retrieving, creating, starting execution, getting execution of tasks using an API client.

    Attributes:
        api_client (ApiClientType): The client responsible for API interactions.

    Methods:
        _get(self, agent_id: Union[UUID, str], task_id: Union[UUID, str]) -> Union[Task, Awaitable[Task]]:
            Retrieves a single task given agent and task IDs.
            Args:
                agent_id (Union[UUID, str]): The UUID of the agent
                task_id (Union[UUID, str]): The UUID of the task
            Returns:
                The task object or an awaitable that resolves to the task object.

        _create(self, agent_id: Union[UUID, str], name: str, description: Optional[str] = None, tools_available: Optional[List[str]] = None, input_schema: Optional[Dict[str, Any]] = None, main: List[WorkflowStep]) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
            Creates a task with the given specifications.
            Args:
                agent_id (Union[UUID, str]): Agent ID
                name (str): Task name
                description (Optional[str]): Task description
                tools_available (Optional[List[str]]): A list of available tools
                input_schema (Optional[Dict[str, Any]]): Input schema
                main (List[WorkflowStep]): A list of workflow steps
            Returns:
                The response indicating creation or an awaitable that resolves to the creation response.

        _get_task_execution(self, task_id: Union[UUID, str], execution_id: Union[UUID, str]) -> Union[List[Execution], Awaitable[List[Execution]]]:
            Retrieves task execution objects given a task and execution IDs
            Args:
                task_id Union[UUID, str]: Task ID
                execution_id (Union[UUID, str]): Execution ID
            Returns:
                A list of Execution objects

        _start_task_execution(self, agent_id: Union[UUID, str], task_id: Union[UUID, str], arguments: Dict[str, Any], status: ExecutionStatus) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
            Starts task execution given agent and task IDs and all the required parameters
            Args:
                agent_id (Union[UUID, str]): Agent ID
                task_id (Union[UUID, str]): Task ID
                arguments (Dict[str, Any]): Task arguments
                status (ExecutionStatus): Task execution status
            Returns:
                The response indicating creation or an awaitable that resolves to the creation response.

        _list(self, agent_id: Union[UUID, str]) -> Union[List[Task], Awaitable[List[Task]]]:
        Retrieves a list of tasks.
        Args:
            agent_id (Union[UUID, str]): Agent ID
        Returns:
            List[Task]: A list of Task objects.
    """

    def _list(
        self, agent_id: Union[UUID, str]
    ) -> Union[List[Task], Awaitable[List[Task]]]:
        """
        Retrieves a list of tasks.

        Args:
            agent_id (Union[UUID, str]): Agent ID
        Returns:
            List[Task]: A list of Task objects.
        """
        assert is_valid_uuid4(agent_id)

        return self.api_client.list_tasks(
            agent_id=agent_id,
        )

    def _create(
        self,
        agent_id: Union[UUID, str],
        *,
        name: str,
        description: Optional[str] = None,
        tools_available: Optional[List[str]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        main: List[WorkflowStep]
    ) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
        """
        Creates a task with the given specifications.

        Args:
            agent_id (Union[UUID, str]): Agent ID
            name (str): Task name
            description (Optional[str]): Task description
            tools_available (Optional[List[str]]): A list of available tools
            input_schema (Optional[Dict[str, Any]]): Input schema
            main (List[WorkflowStep]): A list of workflow steps
        Returns:
            The response indicating creation or an awaitable that resolves to the creation response.
        """
        assert is_valid_uuid4(agent_id)

        return self.api_client.create_task(
            agent_id=str(agent_id),
            name=name,
            description=description,
            tools_available=tools_available,
            input_schema=input_schema,
            main=main,
        )

    def _get(
        self, agent_id: Union[UUID, str], task_id: Union[UUID, str]
    ) -> Union[Task, Awaitable[Task]]:
        """
        Retrieves a single task given agent and task IDs.

        Args:
            agent_id (Union[UUID, str]): The UUID of the agent
            task_id (Union[UUID, str]): The UUID of the task
        Returns:
            The task object or an awaitable that resolves to the task object.
        """
        assert is_valid_uuid4(agent_id)
        assert is_valid_uuid4(task_id)

        return self.api_client.get_task(
            agent_id=str(agent_id),
            task_id=str(task_id),
        )

    def _get_task_execution(
        self, task_id: Union[UUID, str], execution_id: Union[UUID, str]
    ) -> Union[List[Execution], Awaitable[List[Execution]]]:
        """
        Retrieves task execution objects given a task and execution IDs

        Args:
            task_id Union[UUID, str]: Task ID
            execution_id (Union[UUID, str]): Execution ID
        Returns:
            A list of Execution objects
        """
        assert is_valid_uuid4(task_id)
        assert is_valid_uuid4(execution_id)

        return self.api_client.get_task_execution(
            task_id=task_id,
            execution_id=execution_id,
        )

    def _start_task_execution(
        self,
        agent_id: Union[UUID, str],
        task_id: Union[UUID, str],
        *,
        arguments: Dict[str, Any],
        status: ExecutionStatus
    ) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
        """
        Starts task execution given agent and task IDs and all the required parameters

        Args:
            agent_id (Union[UUID, str]): Agent ID
            task_id (Union[UUID, str]): Task ID
            arguments (Dict[str, Any]): Task arguments
            status (ExecutionStatus): Task execution status
        Returns:
            The response indicating creation or an awaitable that resolves to the creation response.
        """
        assert is_valid_uuid4(agent_id)
        assert is_valid_uuid4(task_id)

        return self.api_client.start_task_execution(
            agent_id=agent_id,
            task_id=task_id,
            create_execution_task_id=task_id,
            arguments=arguments,
            status=status,
        )


class TasksManager(BaseTasksManager):
    """
    A class for managing tasks, inheriting from `BaseTasksManager`.

    This class provides functionalities to interact with and manage tasks, including creating, retrieving, start execution and get execution of tasks. It utilizes type annotations to ensure type correctness at runtime using the `beartype` decorator.

    Methods:
        get(self, agent_id: Union[UUID, str], task_id: Union[UUID, str]) -> Task:
            Retrieves a single task given agent and task IDs.
            Args:
                agent_id (Union[UUID, str]): The UUID of the agent
                task_id (Union[UUID, str]): The UUID of the task
            Returns:
                Task: The task object with the corresponding identifier.

        create(self, agent_id: Union[UUID, str], name: str, description: Optional[str] = None, tools_available: Optional[List[str]] = None, input_schema: Optional[Dict[str, Any]] = None, main: List[WorkflowStep]) -> Task:
            Creates a task with the given specifications.
            Args:
                agent_id (Union[UUID, str]): Agent ID
                name (str): Task name
                description (Optional[str]): Task description
                tools_available (Optional[List[str]]): A list of available tools
                input_schema (Optional[Dict[str, Any]]): Input schema
                main (List[WorkflowStep]): A list of workflow steps
            Returns:
                Task: A newly created task object.

        get_task_execution(self, task_id: Union[UUID, str], execution_id: Union[UUID, str]) -> List[Execution]:
            Retrieves task execution objects given a task and execution IDs
            Args:
                task_id Union[UUID, str]: Task ID
                execution_id (Union[UUID, str]): Execution ID
            Returns:
                List[Execution]: A list of Execution objects

        start_task_execution(self, agent_id: Union[UUID, str], task_id: Union[UUID, str], arguments: Dict[str, Any], status: ExecutionStatus) -> Execution:
            Starts task execution given agent and task IDs and all the required parameters
            Args:
                agent_id (Union[UUID, str]): Agent ID
                task_id (Union[UUID, str]): Task ID
                arguments (Dict[str, Any]): Task arguments
                status (ExecutionStatus): Task execution status
            Returns:
                Execution: A newly created execution object

        list(self, agent_id: Union[UUID, str]) -> List[Task]:
            Retrieves a list of tasks.
            Args:
                agent_id (Union[UUID, str]): Agent ID
            Returns:
                List[Task]: A list of Task objects.
    """

    @beartype
    def list(self, agent_id: Union[UUID, str]) -> List[Task]:
        """
        Retrieves a list of tasks.

        Args:
            agent_id (Union[UUID, str]): Agent ID
        Returns:
            List[Task]: A list of Task objects.
        """
        assert is_valid_uuid4(agent_id)

        return cast(
            List[Task],
            self._list(
                agent_id=agent_id,
            ),
        )

    @beartype
    @rewrap_in_class(Task)
    def create(self, **kwargs: TaskCreateArgs) -> Task:
        """
        Creates a task with the given specifications.

        Args:
            agent_id (Union[UUID, str]): Agent ID
            name (str): Task name
            description (Optional[str]): Task description
            tools_available (Optional[List[str]]): A list of available tools
            input_schema (Optional[Dict[str, Any]]): Input schema
            main (List[WorkflowStep]): A list of workflow steps
        Returns:
            Task: A newly created task object.
        """
        return self._create(**kwargs)

    @beartype
    def get(self, agent_id: Union[UUID, str], task_id: Union[UUID, str]) -> Task:
        """
        Retrieves a single task given agent and task IDs.

        Args:
            agent_id (Union[UUID, str]): The UUID of the agent
            task_id (Union[UUID, str]): The UUID of the task
        Returns:
            Task: The task object with the corresponding identifier.
        """
        return self._get(agent_id=agent_id, task_id=task_id)

    @beartype
    def get_task_execution(
        self, task_id: Union[UUID, str], execution_id: Union[UUID, str]
    ) -> List[Execution]:
        """
        Retrieves task execution objects given a task and execution IDs

        Args:
            task_id Union[UUID, str]: Task ID
            execution_id (Union[UUID, str]): Execution ID
        Returns:
            List[Execution]: A list of Execution objects
        """
        return cast(
            List[Execution],
            self._get_task_execution(task_id=task_id, execution_id=execution_id),
        )

    @beartype
    @rewrap_in_class(Execution)
    def start_task_execution(self, **kwargs: StartTaskExecutionArgs) -> Execution:
        """
        Starts task execution given agent and task IDs and all the required parameters

        Args:
            agent_id (Union[UUID, str]): Agent ID
            task_id (Union[UUID, str]): Task ID
            arguments (Dict[str, Any]): Task arguments
            status (ExecutionStatus): Task execution status
        Returns:
            Execution: A newly created execution object
        """
        return self._start_task_execution(**kwargs)


class AsyncTasksManager(BaseTasksManager):
    """
    A class for managing tasks, inheriting from `BaseTasksManager`.

    This class provides asynchronous functionalities to interact with and manage tasks, including creating, retrieving, start execution and get execution of tasks. It utilizes type annotations to ensure type correctness at runtime using the `beartype` decorator.

    Methods:
        get(self, agent_id: Union[UUID, str], task_id: Union[UUID, str]) -> Task:
            Asynchronously retrieves a single task given agent and task IDs.
            Args:
                agent_id (Union[UUID, str]): The UUID of the agent
                task_id (Union[UUID, str]): The UUID of the task
            Returns:
                Task: The task object with the corresponding identifier.

        create(self, agent_id: Union[UUID, str], name: str, description: Optional[str] = None, tools_available: Optional[List[str]] = None, input_schema: Optional[Dict[str, Any]] = None, main: List[WorkflowStep]) -> Task:
            Asynchronously creates a task with the given specifications.
            Args:
                agent_id (Union[UUID, str]): Agent ID
                name (str): Task name
                description (Optional[str]): Task description
                tools_available (Optional[List[str]]): A list of available tools
                input_schema (Optional[Dict[str, Any]]): Input schema
                main (List[WorkflowStep]): A list of workflow steps
            Returns:
                Task: A newly created task object.

        get_task_execution(self, task_id: Union[UUID, str], execution_id: Union[UUID, str]) -> List[Execution]:
            Asynchronously retrieves task execution objects given a task and execution IDs
            Args:
                task_id Union[UUID, str]: Task ID
                execution_id (Union[UUID, str]): Execution ID
            Returns:
                List[Execution]: A list of Execution objects

        start_task_execution(self, agent_id: Union[UUID, str], task_id: Union[UUID, str], arguments: Dict[str, Any], status: ExecutionStatus) -> Execution:
            Asynchronously starts task execution given agent and task IDs and all the required parameters
            Args:
                agent_id (Union[UUID, str]): Agent ID
                task_id (Union[UUID, str]): Task ID
                arguments (Dict[str, Any]): Task arguments
                status (ExecutionStatus): Task execution status
            Returns:
                Execution: A newly created execution object

        list(self, agent_id: Union[UUID, str]) -> List[Task]:
            Asynchronously retrieves a list of tasks.

            Args:
                agent_id (Union[UUID, str]): Agent ID
            Returns:
                List[Task]: A list of Task objects.
    """

    @beartype
    async def list(self, agent_id: Union[UUID, str]) -> List[Task]:
        """
        Asynchronously retrieves a list of tasks.

        Args:
            agent_id (Union[UUID, str]): Agent ID
        Returns:
            List[Task]: A list of Task objects.
        """
        assert is_valid_uuid4(agent_id)

        return await self._list(
            agent_id=agent_id,
        )

    @beartype
    @rewrap_in_class(Task)
    async def create(self, **kwargs: TaskCreateArgs) -> Task:
        """
        Asynchronously creates a task with the given specifications.

        Args:
            agent_id (Union[UUID, str]): Agent ID
            name (str): Task name
            description (Optional[str]): Task description
            tools_available (Optional[List[str]]): A list of available tools
            input_schema (Optional[Dict[str, Any]]): Input schema
            main (List[WorkflowStep]): A list of workflow steps
        Returns:
            Task: A newly created task object.
        """
        return await self._create(**kwargs)

    @beartype
    async def get(self, agent_id: Union[UUID, str], task_id: Union[UUID, str]) -> Task:
        """
        Asynchronously retrieves a single task given agent and task IDs.

        Args:
            agent_id (Union[UUID, str]): The UUID of the agent
            task_id (Union[UUID, str]): The UUID of the task
        Returns:
            Task: The task object with the corresponding identifier.
        """
        return await self._get(agent_id=agent_id, task_id=task_id)

    @beartype
    async def get_task_execution(
        self, task_id: Union[UUID, str], execution_id: Union[UUID, str]
    ) -> List[Execution]:
        """
        Asynchronously retrieves task execution objects given a task and execution IDs

        Args:
            task_id Union[UUID, str]: Task ID
            execution_id (Union[UUID, str]): Execution ID
        Returns:
            List[Execution]: A list of Execution objects
        """
        return await self._get_task_execution(
            task_id=task_id, execution_id=execution_id
        )

    @beartype
    @rewrap_in_class(Execution)
    async def start_task_execution(self, **kwargs: StartTaskExecutionArgs) -> Execution:
        """
        Asynchronously starts task execution given agent and task IDs and all the required parameters

        Args:
            agent_id (Union[UUID, str]): Agent ID
            task_id (Union[UUID, str]): Task ID
            arguments (Dict[str, Any]): Task arguments
            status (ExecutionStatus): Task execution status
        Returns:
            Execution: A newly created execution object
        """
        return await self._start_task_execution(**kwargs)
