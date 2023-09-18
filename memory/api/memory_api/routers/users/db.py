import logging
from memory_api.clients.cozo import client


logger = logging.getLogger(__name__)


def init():
    query = """
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
    
    try:
        client.run(query)
    except Exception as e:
        logger.exception(e)
