import logging
from memory_api.clients.cozo import client


logger = logging.getLogger(__name__)


def init():
    query = """
    :create characters {
        character_id: Uuid,
        updated_at: Validity default [floor(now()), true],
        =>
        name: String,
        about: String default "",
        metadata: Json default {},
        model: String? default null,
        created_at: Float default now(),
    }
    """
    try:
        client.run(query)
    except Exception as e:
        logger.exception(e)
