import logging
from memory_api.clients.cozo import client


logger = logging.getLogger(__name__)


def init():
    query = """
    :create entries {
        session_id: Uuid,
        entry_id: Uuid default rand_uuid_v4(),
        timestamp: Float default now(),
        role: String,
        name: String? default null,
        =>
        content: String,
        token_count: Int,
        processed: Bool default false,
        parent_id: Uuid? default null,
    }

    ::index create entries:by_parent_id {
        parent_id,
        session_id,
    }

    ::index create entries:by_processed {
        processed,
        session_id,
    }
    """
    try:
        client.run(query)
    except Exception as e:
        logger.exception(e)
