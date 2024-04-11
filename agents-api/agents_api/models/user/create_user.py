from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client

from ...common.utils import json


def create_user_query(
    user_id: UUID,
    developer_id: UUID,
    name: str,
    about: str,
    metadata: dict = {},
    client: CozoClient = client,
) -> pd.DataFrame:
    user_id = str(user_id)
    name = json.dumps(name)
    about = json.dumps(about)
    metadata = json.dumps(metadata)

    query = f"""
    {{
        # Then create the user
        ?[user_id, developer_id, name, about, metadata] <- [
            [to_uuid("{user_id}"), to_uuid("{developer_id}"), {name}, {about}, {metadata}]
        ]

        :insert users {{
            developer_id,
            user_id =>
            name,
            about,
            metadata,
        }}
        :returning
    }}"""

    return client.run(query)
