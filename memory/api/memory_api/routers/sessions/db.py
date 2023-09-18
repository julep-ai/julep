import logging
from memory_api.clients.cozo import client


logger = logging.getLogger(__name__)


def init():
    query = """
    :create sessions {
        
    }
    """
    try:
        client.run(query)
    except Exception as e:
        logger.exception(e)
