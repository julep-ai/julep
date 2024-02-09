import logging
from agents_api.clients.cozo import client


logger = logging.getLogger(__name__)


def init():
    query = """
    :create models {
        model_name: String,
        max_length: Int,
        updated_at: Validity default [floor(now()), true],
        =>
        default_settings: Json default {},
    }
    """
    try:
        client.run(query)
    except Exception as e:
        logger.exception(e)
