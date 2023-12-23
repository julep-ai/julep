from .agent.schema import init as agent_init
from .entry.schema import init as entry_init
from .session.schema import init as session_init
from .user.schema import init as user_init


def init():
    agent_init()
    entry_init()
    session_init()
    user_init()
