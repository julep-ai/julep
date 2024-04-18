# Client

[Julep Python SDK Index](../README.md#julep-python-sdk-index) / [Julep](./index.md#julep) / Client

> Auto-generated documentation for [julep.client](../../../../../julep/client.py) module.

- [Client](#client)
  - [AsyncClient](#asyncclient)
  - [Client](#client-1)

## AsyncClient

[Show source in client.py:155](../../../../../julep/client.py#L155)

A class representing an asynchronous client for interacting with various managers.

This class initializes asynchronous managers for agents, users, sessions, documents, memories,
and tools. It requires an API key and a base URL to establish a connection with the backend
service. If these are not explicitly provided, it looks for them in the environment variables.

#### Attributes

- `agents` *AsyncAgentsManager* - Manager for handling agent-related interactions.
- `users` *AsyncUsersManager* - Manager for handling user-related interactions.
- `sessions` *AsyncSessionsManager* - Manager for handling session-related interactions.
- `docs` *AsyncDocsManager* - Manager for handling document-related interactions.
- `memories` *AsyncMemoriesManager* - Manager for handling memory-related interactions.
- `tools` *AsyncToolsManager* - Manager for handling tool-related interactions.
- `chat` *AsyncChat* - A chat manager instance for handling chat interactions (based on OpenAI client).
- `completions` *AsyncCompletions* - A manager instance for handling completions (based on OpenAI client).

#### Raises

- `AssertionError` - If `api_key` or `base_url` is not provided and also not set as an
                environment variable.

#### Notes

The `api_key` and `base_url` can either be passed explicitly or set as environment
variables `JULEP_API_KEY` and `JULEP_API_URL`, respectively.

#### Arguments

- `api_key` *Optional[str]* - The API key required to authenticate with the service.
                         Defaults to the value of the `JULEP_API_KEY` environment variable.
- `base_url` *Optional[str]* - The base URL of the API service.
                          Defaults to the value of the `JULEP_API_URL` environment variable.
- `*args` - Variable length argument list.
- `**kwargs` - Arbitrary keyword arguments.

#### Signature

```python
class AsyncClient:
    @beartype
    def __init__(
        self,
        api_key: Optional[str] = JULEP_API_KEY,
        base_url: Optional[str] = JULEP_API_URL,
        *args,
        **kwargs
    ): ...
```



## Client

[Show source in client.py:39](../../../../../julep/client.py#L39)

A class that encapsulates managers for different aspects of a system and provides an interface for interacting with an API.

This class initializes and makes use of various manager classes to handle agents, users, sessions, documents, memories, and tools. It requires an API key and a base URL to initialize the API client that the managers will use.

Attributes:
    agents (AgentsManager): A manager instance for handling agents.
    users (UsersManager): A manager instance for handling users.
    sessions (SessionsManager): A manager instance for handling sessions.
    docs (DocsManager): A manager instance for handling documents.
    memories (MemoriesManager): A manager instance for handling memories.
    tools (ToolsManager): A manager instance for handling tools.
    chat (Chat): A chat manager instance for handling chat interactions (based on OpenAI client).
    completions (Completions): A manager instance for handling completions (based on OpenAI client).

Args:
    api_key (Optional[str]): The API key needed to authenticate with the API. Defaults to the JULEP_API_KEY environment variable.
    base_url (Optional[str]): The base URL for the API endpoints. Defaults to the JULEP_API_URL environment variable.
    *args: Variable length argument list.
    **kwargs: Arbitrary keyword arguments.

Raises:
    AssertionError: If either `api_key` or `base_url` is not provided and not set as an environment variable.

Note:
    `beartype` decorator is expected to ensure type checking on the parameters during runtime. The constants `JULEP_API_KEY` and `JULEP_API_URL` should be predefined and represent default values for the API key and base URL, respectively, which can be overridden by providing a value at instantiation.

#### Signature

```python
class Client:
    @beartype
    def __init__(
        self,
        api_key: Optional[str] = JULEP_API_KEY,
        base_url: Optional[str] = JULEP_API_URL,
        timeout: int = 300,
        additional_headers: Dict[str, str] = {},
        _httpx_client: Optional[httpx.Client] = None,
        *args,
        **kwargs
    ): ...
```