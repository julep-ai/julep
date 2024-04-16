from typing import Dict, Optional
from urllib.parse import urlparse

from beartype import beartype
import httpx
from openai import AsyncOpenAI, OpenAI
from openai.resources.chat.chat import AsyncChat, Chat
from openai.resources.completions import AsyncCompletions, Completions

# Note: This is just here because fern generates docs where it asks to:
# `from julep_ai.client import AsyncJulepApi, JulepApi`
from .api.client import AsyncJulepApi, JulepApi  # noqa: F401

from .env import JULEP_API_KEY, JULEP_API_URL
from .managers.agent import AgentsManager, AsyncAgentsManager
from .managers.user import UsersManager, AsyncUsersManager

from .managers.doc import DocsManager, AsyncDocsManager

from .managers.memory import MemoriesManager, AsyncMemoriesManager

from .managers.session import SessionsManager, AsyncSessionsManager
from .managers.tool import ToolsManager, AsyncToolsManager
from .utils.openai_patch import (
    patch_chat_acreate,
    patch_chat_create,
    patch_completions_acreate,
    patch_completions_create,
)

# See Note above
__all__ = ["AsyncJulepApi", "JulepApi", "Client", "AsyncClient"]


def get_base_url(url):
    return f"{urlparse(url).scheme}://{urlparse(url).netloc}"


class Client:
    """
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
    """

    agents: AgentsManager
    users: UsersManager
    sessions: SessionsManager
    docs: DocsManager
    memories: MemoriesManager
    tools: ToolsManager

    chat: Chat
    completions: Completions

    @beartype
    def __init__(
        self,
        api_key: Optional[str] = JULEP_API_KEY,
        base_url: Optional[str] = JULEP_API_URL,
        timeout: int = 300,
        additional_headers: Dict[str, str] = {},
        _httpx_client: Optional[httpx.Client] = None,
        *args,
        **kwargs,
    ):
        """
        Initialize a new client object with the given API key and base URL.

            Args:
                api_key (Optional[str]): The API key for authentication. If not provided,
                    the default is taken from the environment variable JULEP_API_KEY.
                base_url (Optional[str]): The base URL for the API endpoints. If not provided,
                    the default is taken from the environment variable JULEP_API_URL.
                *args: Variable length argument list.
                **kwargs: Arbitrary keyword arguments.

            Raises:
                AssertionError: If either `api_key` or `base_url` is None, indicating they have
                    not been provided and are not set as environment variables.

            Note:
                This constructor populates the client with different resource managers like
                agents, users, sessions, docs, memories, and tools, by initializing respective
                manager classes with the provided API client configuration.
        """
        assert (
            api_key is not None
        ), "api_key must be provided or set as env var JULEP_API_KEY"
        assert (
            base_url is not None
        ), "base_url must be provided or set as env var JULEP_API_URL"

        # Create an httpz client that follows redirects and has a timeout
        httpx_client = _httpx_client or httpx.Client(
            timeout=timeout,
            headers=additional_headers,
            follow_redirects=True,
        )

        self._api_client = JulepApi(
            api_key=f"Bearer {api_key}",
            base_url=base_url,
            httpx_client=httpx_client,
            *args,
            **kwargs,
        )

        self.agents = AgentsManager(api_client=self._api_client)
        self.users = UsersManager(api_client=self._api_client)
        self.sessions = SessionsManager(api_client=self._api_client)
        self.docs = DocsManager(api_client=self._api_client)
        self.memories = MemoriesManager(api_client=self._api_client)
        self.tools = ToolsManager(api_client=self._api_client)

        # Set up the OpenAI client
        openai_base_url = f"{get_base_url(base_url)}/v1"
        self._openai_client = OpenAI(
            api_key=api_key,
            base_url=openai_base_url,
            *args,
            **kwargs,
        )

        # Patch the OpenAI client to pass non-openai params
        patch_chat_create(self._openai_client)
        patch_completions_create(self._openai_client)

        self.chat = self._openai_client.chat
        self.completions = self._openai_client.completions


class AsyncClient:
    """
    A class representing an asynchronous client for interacting with various managers.

    This class initializes asynchronous managers for agents, users, sessions, documents, memories,
    and tools. It requires an API key and a base URL to establish a connection with the backend
    service. If these are not explicitly provided, it looks for them in the environment variables.

    Attributes:
        agents (AsyncAgentsManager): Manager for handling agent-related interactions.
        users (AsyncUsersManager): Manager for handling user-related interactions.
        sessions (AsyncSessionsManager): Manager for handling session-related interactions.
        docs (AsyncDocsManager): Manager for handling document-related interactions.
        memories (AsyncMemoriesManager): Manager for handling memory-related interactions.
        tools (AsyncToolsManager): Manager for handling tool-related interactions.
        chat (AsyncChat): A chat manager instance for handling chat interactions (based on OpenAI client).
        completions (AsyncCompletions): A manager instance for handling completions (based on OpenAI client).

    Raises:
        AssertionError: If `api_key` or `base_url` is not provided and also not set as an
                        environment variable.

    Note:
        The `api_key` and `base_url` can either be passed explicitly or set as environment
        variables `JULEP_API_KEY` and `JULEP_API_URL`, respectively.

    Args:
        api_key (Optional[str]): The API key required to authenticate with the service.
                                 Defaults to the value of the `JULEP_API_KEY` environment variable.
        base_url (Optional[str]): The base URL of the API service.
                                  Defaults to the value of the `JULEP_API_URL` environment variable.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """

    agents: AsyncAgentsManager
    users: AsyncUsersManager
    sessions: AsyncSessionsManager
    docs: AsyncDocsManager
    memories: AsyncMemoriesManager
    tools: AsyncToolsManager

    chat: AsyncChat
    completions: AsyncCompletions

    @beartype
    def __init__(
        self,
        api_key: Optional[str] = JULEP_API_KEY,
        base_url: Optional[str] = JULEP_API_URL,
        *args,
        **kwargs,
    ):
        """
        Initialize the client with the provided API key and base URL.

            This constructor sets up an asynchronous client for various service managers
            like agents, users, sessions, documents, memories, and tools.

            The 'beartype' decorator is used for runtime type checking on the given arguments.

            The `api_key` and `base_url` must either be provided as arguments or set as
            environment variables (`JULEP_API_KEY`, `JULEP_API_URL` respectively).

            Args:
                api_key (Optional[str]): The API key for authentication. If not provided,
                    it should be set as the environment variable 'JULEP_API_KEY'.
                base_url (Optional[str]): The base URL of the API. If not provided,
                    it should be set as the environment variable 'JULEP_API_URL'.
                *args: Variable length argument list to be passed to the `AsyncJulepApi`.
                **kwargs: Arbitrary keyword arguments to be passed to the `AsyncJulepApi`.

            Raises:
                AssertionError: If `api_key` or `base_url` is not supplied either
                    through function arguments or environment variables.

            Note:
                The actual function signature does not explicitly show the environment variables
                (`JULEP_API_KEY`, `JULEP_API_URL`) as default values for `api_key` and `base_url`
                due to the limitations in using environment variables as default function argument values.
                Instead, they must be handled within the body of the function.
        """
        assert (
            api_key is not None
        ), "api_key must be provided or set as env var JULEP_API_KEY"
        assert (
            base_url is not None
        ), "base_url must be provided or set as env var JULEP_API_URL"

        self._api_client = AsyncJulepApi(
            api_key=f"Bearer {api_key}", base_url=base_url, *args, **kwargs
        )

        self.agents = AsyncAgentsManager(api_client=self._api_client)
        self.users = AsyncUsersManager(api_client=self._api_client)
        self.sessions = AsyncSessionsManager(api_client=self._api_client)
        self.docs = AsyncDocsManager(api_client=self._api_client)
        self.memories = AsyncMemoriesManager(api_client=self._api_client)
        self.tools = AsyncToolsManager(api_client=self._api_client)

        # Set up the OpenAI client
        openai_base_url = f"{get_base_url(base_url)}/v1"
        self._openai_client = AsyncOpenAI(
            api_key=api_key,
            base_url=openai_base_url,
            *args,
            **kwargs,
        )

        # Patch the OpenAI client to pass non-openai params
        patch_chat_acreate(self._openai_client)
        patch_completions_acreate(self._openai_client)

        self.chat = self._openai_client.chat
        self.completions = self._openai_client.completions
