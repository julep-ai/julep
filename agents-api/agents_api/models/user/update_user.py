from uuid import UUID


from ..utils import cozo_query
from ...common.utils.cozo import cozo_process_mutate_data


@cozo_query
def update_user_query(
    developer_id: UUID, user_id: UUID, **update_data
) -> tuple[str, dict]:
    """Updates user information in the 'cozodb' database.

    Parameters:
        developer_id (UUID): The developer's unique identifier.
        user_id (UUID): The user's unique identifier.
        client (CozoClient): The Cozo database client instance.
        **update_data: Arbitrary keyword arguments representing the data to update.

    Returns:
        pd.DataFrame: A DataFrame containing the result of the update operation.
    """
    user_id = str(user_id)
    developer_id = str(developer_id)
    # Prepares the update data by filtering out None values and adding user_id and developer_id.
    user_update_cols, user_update_vals = cozo_process_mutate_data(
        {
            **{k: v for k, v in update_data.items() if v is not None},
            "user_id": user_id,
            "developer_id": developer_id,
        }
    )

    assertion_query = """
        ?[developer_id, user_id] :=
            *users {
                developer_id,
                user_id,
            },
            developer_id = to_uuid($developer_id),
            user_id = to_uuid($user_id),

        # Assertion to ensure the user exists before updating.
        :assert some
    """

    # Constructs the update operation for the user, setting new values and updating 'updated_at'.
    query = f"""
        # update the user
        # This line updates the user's information based on the provided columns and values.
        input[{user_update_cols}] <- $user_update_vals
        original[created_at] := *users{{
            developer_id: to_uuid($developer_id),
            user_id: to_uuid($user_id),
            created_at,
        }},

        ?[created_at, updated_at, {user_update_cols}] :=
            input[{user_update_cols}],
            original[created_at],
            updated_at = now(),

        :put users {{
            created_at,
            updated_at,
            {user_update_cols}
        }}
        :returning
    """

    query = "{" + assertion_query + "} {" + query + "}"
    # Combines the assertion and update queries.

    return (
        query,
        {
            "user_update_vals": user_update_vals,
            "developer_id": developer_id,
            "user_id": user_id,
        },
    )
