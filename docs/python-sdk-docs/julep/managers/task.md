# Task

[Julep Python SDK Index](../../README.md#julep-python-sdk-index) / [Julep](../index.md#julep) / [Managers](./index.md#managers) / Task

> Auto-generated documentation for [julep.managers.task](../../../../../../julep/managers/task.py) module.

- [Task](#task)
  - [AsyncTasksManager](#asynctasksmanager)
  - [BaseTasksManager](#basetasksmanager)
  - [StartTaskExecutionArgs](#starttaskexecutionargs)
  - [TaskCreateArgs](#taskcreateargs)
  - [TasksManager](#tasksmanager)

## AsyncTasksManager

[Show source in task.py:348](../../../../../../julep/managers/task.py#L348)

A class for managing tasks, inheriting from [BaseTasksManager](#basetasksmanager).

This class provides asynchronous functionalities to interact with and manage tasks, including creating, retrieving, start execution and get execution of tasks. It utilizes type annotations to ensure type correctness at runtime using the `beartype` decorator.

#### Methods

- `get(self,` *agent_id* - Union[UUID, str], task_id: Union[UUID, str]) -> Task:
    Asynchronously retrieves a single task given agent and task IDs.

#### Arguments

agent_id (Union[UUID, str]): The UUID of the agent
task_id (Union[UUID, str]): The UUID of the task
agent_id (Union[UUID, str]): Agent ID
- `name` *str* - Task name
- `description` *Optional[str]* - Task description
- `tools_available` *Optional[List[str]]* - A list of available tools
input_schema (Optional[Dict[str, Any]]): Input schema
- `main` *List[WorkflowStep]* - A list of workflow steps
task_id Union[UUID, str]: Task ID
execution_id (Union[UUID, str]): Execution ID
agent_id (Union[UUID, str]): Agent ID
task_id (Union[UUID, str]): Task ID
arguments (Dict[str, Any]): Task arguments
- `status` *ExecutionStatus* - Task execution status
agent_id (Union[UUID, str]): Agent ID

#### Returns

- `Task` - The task object with the corresponding identifier.

- `create(self,` *agent_id* - Union[UUID, str], name: str, description: Optional[str] = None, tools_available: Optional[List[str]] = None, input_schema: Optional[Dict[str, Any]] = None, main: List[WorkflowStep]) -> Task:
    Asynchronously creates a task with the given specifications.
        - `Task` - A newly created task object.

- `get_task_execution(self,` *task_id* - Union[UUID, str], execution_id: Union[UUID, str]) -> List[Execution]:
    Asynchronously retrieves task execution objects given a task and execution IDs
        - `List[Execution]` - A list of Execution objects

- `start_task_execution(self,` *agent_id* - Union[UUID, str], task_id: Union[UUID, str], arguments: Dict[str, Any], status: ExecutionStatus) -> Execution:
    Asynchronously starts task execution given agent and task IDs and all the required parameters
        - `Execution` - A newly created execution object

- `list(self,` *agent_id* - Union[UUID, str]) -> List[Task]:
    Asynchronously retrieves a list of tasks.

- `List[Task]` - A list of Task objects.

#### Signature

```python
class AsyncTasksManager(BaseTasksManager): ...
```

#### See also

- [BaseTasksManager](#basetasksmanager)

### AsyncTasksManager().create

[Show source in task.py:418](../../../../../../julep/managers/task.py#L418)

Asynchronously creates a task with the given specifications.

#### Arguments

agent_id (Union[UUID, str]): Agent ID
- `name` *str* - Task name
- `description` *Optional[str]* - Task description
- `tools_available` *Optional[List[str]]* - A list of available tools
input_schema (Optional[Dict[str, Any]]): Input schema
- `main` *List[WorkflowStep]* - A list of workflow steps

#### Returns

- `Task` - A newly created task object.

#### Signature

```python
@beartype
@rewrap_in_class(Task)
async def create(self, **kwargs: TaskCreateArgs) -> Task: ...
```

#### See also

- [TaskCreateArgs](#taskcreateargs)

### AsyncTasksManager().get

[Show source in task.py:436](../../../../../../julep/managers/task.py#L436)

Asynchronously retrieves a single task given agent and task IDs.

#### Arguments

agent_id (Union[UUID, str]): The UUID of the agent
task_id (Union[UUID, str]): The UUID of the task

#### Returns

- `Task` - The task object with the corresponding identifier.

#### Signature

```python
@beartype
async def get(self, agent_id: Union[UUID, str], task_id: Union[UUID, str]) -> Task: ...
```

### AsyncTasksManager().get_task_execution

[Show source in task.py:449](../../../../../../julep/managers/task.py#L449)

Asynchronously retrieves task execution objects given a task and execution IDs

#### Arguments

task_id Union[UUID, str]: Task ID
execution_id (Union[UUID, str]): Execution ID

#### Returns

- `List[Execution]` - A list of Execution objects

#### Signature

```python
@beartype
async def get_task_execution(
    self, task_id: Union[UUID, str], execution_id: Union[UUID, str]
) -> List[Execution]: ...
```

### AsyncTasksManager().list

[Show source in task.py:402](../../../../../../julep/managers/task.py#L402)

Asynchronously retrieves a list of tasks.

#### Arguments

agent_id (Union[UUID, str]): Agent ID

#### Returns

- `List[Task]` - A list of Task objects.

#### Signature

```python
@beartype
async def list(self, agent_id: Union[UUID, str]) -> List[Task]: ...
```

### AsyncTasksManager().start_task_execution

[Show source in task.py:466](../../../../../../julep/managers/task.py#L466)

Asynchronously starts task execution given agent and task IDs and all the required parameters

#### Arguments

agent_id (Union[UUID, str]): Agent ID
task_id (Union[UUID, str]): Task ID
arguments (Dict[str, Any]): Task arguments
- `status` *ExecutionStatus* - Task execution status

#### Returns

- `Execution` - A newly created execution object

#### Signature

```python
@beartype
@rewrap_in_class(Execution)
async def start_task_execution(self, **kwargs: StartTaskExecutionArgs) -> Execution: ...
```

#### See also

- [StartTaskExecutionArgs](#starttaskexecutionargs)



## BaseTasksManager

[Show source in task.py:32](../../../../../../julep/managers/task.py#L32)

A class responsible for managing task entities.

This manager handles CRUD operations for tasks including retrieving, creating, starting execution, getting execution of tasks using an API client.

#### Attributes

- `api_client` *ApiClientType* - The client responsible for API interactions.

#### Methods

- `_get(self,` *agent_id* - Union[UUID, str], task_id: Union[UUID, str]) -> Union[Task, Awaitable[Task]]:
    Retrieves a single task given agent and task IDs.

#### Arguments

    agent_id (Union[UUID, str]): The UUID of the agent
    task_id (Union[UUID, str]): The UUID of the task
    agent_id (Union[UUID, str]): Agent ID
    - `name` *str* - Task name
    - `description` *Optional[str]* - Task description
    - `tools_available` *Optional[List[str]]* - A list of available tools
    input_schema (Optional[Dict[str, Any]]): Input schema
    - `main` *List[WorkflowStep]* - A list of workflow steps
    task_id Union[UUID, str]: Task ID
    execution_id (Union[UUID, str]): Execution ID
    agent_id (Union[UUID, str]): Agent ID
    task_id (Union[UUID, str]): Task ID
    arguments (Dict[str, Any]): Task arguments
    - `status` *ExecutionStatus* - Task execution status
agent_id (Union[UUID, str]): Agent ID

#### Returns

The task object or an awaitable that resolves to the task object.

- `_create(self,` *agent_id* - Union[UUID, str], name: str, description: Optional[str] = None, tools_available: Optional[List[str]] = None, input_schema: Optional[Dict[str, Any]] = None, main: List[WorkflowStep]) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
    Creates a task with the given specifications.
        The response indicating creation or an awaitable that resolves to the creation response.

- `_get_task_execution(self,` *task_id* - Union[UUID, str], execution_id: Union[UUID, str]) -> Union[List[Execution], Awaitable[List[Execution]]]:
    Retrieves task execution objects given a task and execution IDs
        A list of Execution objects

- `_start_task_execution(self,` *agent_id* - Union[UUID, str], task_id: Union[UUID, str], arguments: Dict[str, Any], status: ExecutionStatus) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
    Starts task execution given agent and task IDs and all the required parameters
        The response indicating creation or an awaitable that resolves to the creation response.

- `_list(self,` *agent_id* - Union[UUID, str]) -> Union[List[Task], Awaitable[List[Task]]]:
Retrieves a list of tasks.
    - `List[Task]` - A list of Task objects.

#### Signature

```python
class BaseTasksManager(BaseManager): ...
```

### BaseTasksManager()._create

[Show source in task.py:105](../../../../../../julep/managers/task.py#L105)

Creates a task with the given specifications.

#### Arguments

agent_id (Union[UUID, str]): Agent ID
- `name` *str* - Task name
- `description` *Optional[str]* - Task description
- `tools_available` *Optional[List[str]]* - A list of available tools
input_schema (Optional[Dict[str, Any]]): Input schema
- `main` *List[WorkflowStep]* - A list of workflow steps

#### Returns

The response indicating creation or an awaitable that resolves to the creation response.

#### Signature

```python
def _create(
    self,
    agent_id: Union[UUID, str],
    name: str,
    description: Optional[str] = None,
    tools_available: Optional[List[str]] = None,
    input_schema: Optional[Dict[str, Any]] = None,
    main: List[WorkflowStep],
) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]: ...
```

### BaseTasksManager()._get

[Show source in task.py:139](../../../../../../julep/managers/task.py#L139)

Retrieves a single task given agent and task IDs.

#### Arguments

agent_id (Union[UUID, str]): The UUID of the agent
task_id (Union[UUID, str]): The UUID of the task

#### Returns

The task object or an awaitable that resolves to the task object.

#### Signature

```python
def _get(
    self, agent_id: Union[UUID, str], task_id: Union[UUID, str]
) -> Union[Task, Awaitable[Task]]: ...
```

### BaseTasksManager()._get_task_execution

[Show source in task.py:159](../../../../../../julep/managers/task.py#L159)

Retrieves task execution objects given a task and execution IDs

#### Arguments

task_id Union[UUID, str]: Task ID
execution_id (Union[UUID, str]): Execution ID

#### Returns

A list of Execution objects

#### Signature

```python
def _get_task_execution(
    self, task_id: Union[UUID, str], execution_id: Union[UUID, str]
) -> Union[List[Execution], Awaitable[List[Execution]]]: ...
```

### BaseTasksManager()._list

[Show source in task.py:88](../../../../../../julep/managers/task.py#L88)

Retrieves a list of tasks.

#### Arguments

agent_id (Union[UUID, str]): Agent ID

#### Returns

- `List[Task]` - A list of Task objects.

#### Signature

```python
def _list(
    self, agent_id: Union[UUID, str]
) -> Union[List[Task], Awaitable[List[Task]]]: ...
```

### BaseTasksManager()._start_task_execution

[Show source in task.py:179](../../../../../../julep/managers/task.py#L179)

Starts task execution given agent and task IDs and all the required parameters

#### Arguments

agent_id (Union[UUID, str]): Agent ID
task_id (Union[UUID, str]): Task ID
arguments (Dict[str, Any]): Task arguments
- `status` *ExecutionStatus* - Task execution status

#### Returns

The response indicating creation or an awaitable that resolves to the creation response.

#### Signature

```python
def _start_task_execution(
    self,
    agent_id: Union[UUID, str],
    task_id: Union[UUID, str],
    arguments: Dict[str, Any],
    status: ExecutionStatus,
) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]: ...
```



## StartTaskExecutionArgs

[Show source in task.py:25](../../../../../../julep/managers/task.py#L25)

#### Signature

```python
class StartTaskExecutionArgs(TypedDict): ...
```



## TaskCreateArgs

[Show source in task.py:16](../../../../../../julep/managers/task.py#L16)

#### Signature

```python
class TaskCreateArgs(TypedDict): ...
```



## TasksManager

[Show source in task.py:210](../../../../../../julep/managers/task.py#L210)

A class for managing tasks, inheriting from [BaseTasksManager](#basetasksmanager).

This class provides functionalities to interact with and manage tasks, including creating, retrieving, start execution and get execution of tasks. It utilizes type annotations to ensure type correctness at runtime using the `beartype` decorator.

#### Methods

- `get(self,` *agent_id* - Union[UUID, str], task_id: Union[UUID, str]) -> Task:
    Retrieves a single task given agent and task IDs.

#### Arguments

agent_id (Union[UUID, str]): The UUID of the agent
task_id (Union[UUID, str]): The UUID of the task
agent_id (Union[UUID, str]): Agent ID
- `name` *str* - Task name
- `description` *Optional[str]* - Task description
- `tools_available` *Optional[List[str]]* - A list of available tools
input_schema (Optional[Dict[str, Any]]): Input schema
- `main` *List[WorkflowStep]* - A list of workflow steps
task_id Union[UUID, str]: Task ID
execution_id (Union[UUID, str]): Execution ID
agent_id (Union[UUID, str]): Agent ID
task_id (Union[UUID, str]): Task ID
arguments (Dict[str, Any]): Task arguments
- `status` *ExecutionStatus* - Task execution status
agent_id (Union[UUID, str]): Agent ID

#### Returns

- `Task` - The task object with the corresponding identifier.

- `create(self,` *agent_id* - Union[UUID, str], name: str, description: Optional[str] = None, tools_available: Optional[List[str]] = None, input_schema: Optional[Dict[str, Any]] = None, main: List[WorkflowStep]) -> Task:
    Creates a task with the given specifications.
        - `Task` - A newly created task object.

- `get_task_execution(self,` *task_id* - Union[UUID, str], execution_id: Union[UUID, str]) -> List[Execution]:
    Retrieves task execution objects given a task and execution IDs
        - `List[Execution]` - A list of Execution objects

- `start_task_execution(self,` *agent_id* - Union[UUID, str], task_id: Union[UUID, str], arguments: Dict[str, Any], status: ExecutionStatus) -> Execution:
    Starts task execution given agent and task IDs and all the required parameters
        - `Execution` - A newly created execution object

- `list(self,` *agent_id* - Union[UUID, str]) -> List[Task]:
    Retrieves a list of tasks.
        - `List[Task]` - A list of Task objects.

#### Signature

```python
class TasksManager(BaseTasksManager): ...
```

#### See also

- [BaseTasksManager](#basetasksmanager)

### TasksManager().create

[Show source in task.py:282](../../../../../../julep/managers/task.py#L282)

Creates a task with the given specifications.

#### Arguments

agent_id (Union[UUID, str]): Agent ID
- `name` *str* - Task name
- `description` *Optional[str]* - Task description
- `tools_available` *Optional[List[str]]* - A list of available tools
input_schema (Optional[Dict[str, Any]]): Input schema
- `main` *List[WorkflowStep]* - A list of workflow steps

#### Returns

- `Task` - A newly created task object.

#### Signature

```python
@beartype
@rewrap_in_class(Task)
def create(self, **kwargs: TaskCreateArgs) -> Task: ...
```

#### See also

- [TaskCreateArgs](#taskcreateargs)

### TasksManager().get

[Show source in task.py:300](../../../../../../julep/managers/task.py#L300)

Retrieves a single task given agent and task IDs.

#### Arguments

agent_id (Union[UUID, str]): The UUID of the agent
task_id (Union[UUID, str]): The UUID of the task

#### Returns

- `Task` - The task object with the corresponding identifier.

#### Signature

```python
@beartype
def get(self, agent_id: Union[UUID, str], task_id: Union[UUID, str]) -> Task: ...
```

### TasksManager().get_task_execution

[Show source in task.py:313](../../../../../../julep/managers/task.py#L313)

Retrieves task execution objects given a task and execution IDs

#### Arguments

task_id Union[UUID, str]: Task ID
execution_id (Union[UUID, str]): Execution ID

#### Returns

- `List[Execution]` - A list of Execution objects

#### Signature

```python
@beartype
def get_task_execution(
    self, task_id: Union[UUID, str], execution_id: Union[UUID, str]
) -> List[Execution]: ...
```

### TasksManager().list

[Show source in task.py:263](../../../../../../julep/managers/task.py#L263)

Retrieves a list of tasks.

#### Arguments

agent_id (Union[UUID, str]): Agent ID

#### Returns

- `List[Task]` - A list of Task objects.

#### Signature

```python
@beartype
def list(self, agent_id: Union[UUID, str]) -> List[Task]: ...
```

### TasksManager().start_task_execution

[Show source in task.py:331](../../../../../../julep/managers/task.py#L331)

Starts task execution given agent and task IDs and all the required parameters

#### Arguments

agent_id (Union[UUID, str]): Agent ID
task_id (Union[UUID, str]): Task ID
arguments (Dict[str, Any]): Task arguments
- `status` *ExecutionStatus* - Task execution status

#### Returns

- `Execution` - A newly created execution object

#### Signature

```python
@beartype
@rewrap_in_class(Execution)
def start_task_execution(self, **kwargs: StartTaskExecutionArgs) -> Execution: ...
```

#### See also

- [StartTaskExecutionArgs](#starttaskexecutionargs)