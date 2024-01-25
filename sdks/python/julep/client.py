from typing import Optional

from beartype import beartype

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

# See Note above
__all__ = ["AsyncJulepApi", "JulepApi", "Client", "AsyncClient"]


class Client:
    agents: AgentsManager
    users: UsersManager
    sessions: SessionsManager
    docs: DocsManager
    memories: MemoriesManager
    tools: ToolsManager

    @beartype
    def __init__(
        self,
        api_key: Optional[str] = JULEP_API_KEY,
        base_url: Optional[str] = JULEP_API_URL,
        *args,
        **kwargs
    ):
        assert (
            api_key is not None
        ), "api_key must be provided or set as env var JULEP_API_KEY"
        assert (
            base_url is not None
        ), "base_url must be provided or set as env var JULEP_API_URL"

        self._api_client = JulepApi(api_key=api_key, base_url=base_url, *args, **kwargs)

        self.agents = AgentsManager(api_client=self._api_client)
        self.users = UsersManager(api_client=self._api_client)
        self.sessions = SessionsManager(api_client=self._api_client)
        self.docs = DocsManager(api_client=self._api_client)
        self.memories = MemoriesManager(api_client=self._api_client)
        self.tools = ToolsManager(api_client=self._api_client)


class AsyncClient:
    agents: AsyncAgentsManager
    users: AsyncUsersManager
    sessions: AsyncSessionsManager
    docs: AsyncDocsManager
    memories: AsyncMemoriesManager
    tools: AsyncToolsManager

    @beartype
    def __init__(
        self,
        api_key: Optional[str] = JULEP_API_KEY,
        base_url: Optional[str] = JULEP_API_URL,
        *args,
        **kwargs
    ):
        assert (
            api_key is not None
        ), "api_key must be provided or set as env var JULEP_API_KEY"
        assert (
            base_url is not None
        ), "base_url must be provided or set as env var JULEP_API_URL"

        self._api_client = AsyncJulepApi(
            api_key=api_key, base_url=base_url, *args, **kwargs
        )

        self.agents = AsyncAgentsManager(api_client=self._api_client)
        self.users = AsyncUsersManager(api_client=self._api_client)
        self.sessions = AsyncSessionsManager(api_client=self._api_client)
        self.docs = AsyncDocsManager(api_client=self._api_client)
        self.memories = AsyncMemoriesManager(api_client=self._api_client)
        self.tools = AsyncToolsManager(api_client=self._api_client)
