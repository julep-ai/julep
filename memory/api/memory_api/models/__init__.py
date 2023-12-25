from memory_api.clients.cozo import client

from .agent.schema import init as agent_init
from .entry.schema import init as entry_init
from .session.schema import init as session_init
from .user.schema import init as user_init


def init(client=client):
    agent_init(client)
    entry_init(client)
    session_init(client)
    user_init(client)
