# ruff: noqa: F401, F403, F405
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, Field
from pydantic_partial import create_partial_model

from ..common.utils.datetime import utcnow
from .Agents import *
from .Chat import *
from .Common import *
from .Docs import *
from .Entries import *
from .Executions import *
from .Jobs import *
from .Sessions import *
from .Tasks import *
from .Tools import *
from .Users import *

CreateToolRequest = UpdateToolRequest
CreateOrUpdateAgentRequest = UpdateAgentRequest
CreateOrUpdateUserRequest = UpdateUserRequest
CreateOrUpdateSessionRequest = CreateSessionRequest
CreateOrUpdateTaskRequest = CreateTaskRequest

CreateTransitionRequest = create_partial_model(
    Transition,
    # The following fields are optional
    "id",
    "execution_id",
    "created_at",
    "updated_at",
    "metadata",
)

ChatMLRole = BaseEntry.model_fields["role"].annotation


class CreateEntryRequest(BaseEntry):
    timestamp: Annotated[
        float, Field(ge=0.0, default_factory=lambda: utcnow().timestamp())
    ]


def make_session(
    *,
    agents: list[UUID],
    users: list[UUID],
    **data: dict,
) -> Session:
    """
    Create a new session object.
    """
    cls, participants = None, {}
    match (len(agents), len(users)):
        case (0, _):
            raise ValueError("At least one agent must be provided.")
        case (1, 0):
            cls = SingleAgentNoUserSession
            participants = {"agent": agents[0]}
        case (1, 1):
            cls = SingleAgentSingleUserSession
            participants = {"agent": agents[0], "user": users[0]}
        case (1, u) if u > 1:
            cls = SingleAgentMultiUserSession
            participants = {"agent": agents[0], "users": users}
        case _:
            cls = MultiAgentMultiUserSession
            participants = {"agents": agents, "users": users}

    return cls(**{**data, **participants})
