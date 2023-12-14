import logging
from pydantic import UUID4
from memory_api.clients.cozo import client
from .protocol import UserInformation


logger = logging.getLogger(__name__)


def init():
    users = """
    :create users {
        user_id: Uuid,
        updated_at: Validity default [floor(now()), true],
        =>
        name: String,
        email: String,
        about: String default "",
        metadata: Json default {},
        created_at: Float default now(),
    }"""

    additional_info = """
    :create additional_information {
        user_id: Uuid,
        title: String,
        content: String,
        vector: <F32; 768>,
    }"""
    
    try:
        for query in [users, additional_info]:
            client.run(query)
    except Exception as e:
        logger.exception(e)


def get_user_data(user_id: UUID4):
    get_query = f"""
        input[user_id] <- [[to_uuid("{user_id}")]]

        ?[
            user_id,
            name,
            email,
            about,
            metadata,
            updated_at,
            created_at,
        ] := input[user_id],
            *users {{
                user_id,
                name,
                email,
                about,
                metadata,
                updated_at: validity,
                created_at,
                @ "NOW"
            }}, updated_at = to_int(validity)"""

    res = [row.to_dict() for _, row in client.run(get_query).iterrows()][0]