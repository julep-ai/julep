import logging
from memory_api.clients.cozo import client


logger = logging.getLogger(__name__)


def init():
    query = """
    :create sessions {
        character_id: Uuid,
        user_id: Uuid? default null,
        session_id: Uuid,
        updated_at: Validity default [floor(now()), true],
        =>
        situation: String,
        summary: String? default null,
        metadata: Json default {},
        created_at: Float default now(),
    }
    """
    try:
        client.run(query)
    except Exception as e:
        logger.exception(e)
