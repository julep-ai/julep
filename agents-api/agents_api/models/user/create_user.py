"""
This module contains the functionality for creating a new user in the CozoDB database.
It defines a query for inserting user data into the 'users' relation.
"""

from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


"""
Constructs and executes a datalog query to create a new user in the CozoDB database.

Parameters:
    user_id (UUID): The unique identifier for the user.
    developer_id (UUID): The unique identifier for the developer creating the user.
    name (str): The name of the user.
    about (str): A brief description about the user.
    metadata (dict, optional): Additional metadata about the user. Defaults to an empty dict.
    client (CozoClient, optional): The CozoDB client instance to run the query. Defaults to a pre-configured client instance.

Returns:
    pd.DataFrame: A DataFrame containing the result of the query execution.
"""


def create_user_query(
    user_id: UUID,
    developer_id: UUID,
    name: str,
    about: str,
    metadata: dict = {},
    client: CozoClient = client,
) -> pd.DataFrame:
    query = """
    {
        # Then create the user
        ?[user_id, developer_id, name, about, metadata] <- [
            [to_uuid($user_id), to_uuid($developer_id), $name, $about, $metadata]
        ]

        :insert users {
            developer_id,
            user_id =>
            name,
            about,
            metadata,
        }
        :returning
    }"""

    return client.run(
        query,
        {
            "user_id": str(user_id),
            "developer_id": str(developer_id),
            "name": name,
            "about": about,
            "metadata": metadata,
        },
    )
