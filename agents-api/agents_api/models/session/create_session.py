from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client
from ...common.utils import json


def create_session_query(
    session_id: UUID,
    developer_id: UUID,
    agent_id: UUID,
    user_id: UUID | None,
    situation: str | None,
    metadata: dict = {},
    client: CozoClient = client,
) -> pd.DataFrame:
    user_create_query = f'to_uuid("{user_id}")' if user_id else "null"

    query = f"""
    {{
        # Create a new session lookup
        ?[session_id, agent_id, user_id] <- [[
            to_uuid("{session_id}"),
            to_uuid("{agent_id}"),
            {user_create_query},
        ]]

        :insert session_lookup {{
            agent_id,
            user_id,
            session_id,
        }}
    }} {{
        # Create a new session
        ?[session_id, developer_id, situation, metadata] <- [[
            to_uuid("{session_id}"),
            to_uuid("{developer_id}"),
            {json.dumps(situation)},
            {json.dumps(metadata)},
        ]]

        :insert sessions {{
            developer_id,
            session_id,
            situation,
            metadata,
        }}
        :returning
     }}"""

    return client.run(query)
