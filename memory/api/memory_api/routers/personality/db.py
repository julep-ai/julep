import json
import logging
from memory_api.clients.cozo import client
from pydantic import UUID4
from pandas import DataFrame


logger = logging.getLogger(__name__)


def create_account_query(user_id: UUID4, account_id: str) -> DataFrame:
    query = f"""
    ?[
        user_id,
        account_id,
    ] <- [[
    to_uuid("{user_id}"),
    "{account_id}",
    ]]

    :put user_principles {{
        user_id,
        account_id,
    }}
    """

    return client.run(query)


def get_account_query(user_id: UUID4) -> DataFrame:
    query = f"""
    input[user_id] <- [[
        to_uuid("{user_id}"),
    ]]

    ?[
        user_id,
        account_id,
        full,
        processed_at,
        scores,
    ] := input[user_id],
    *user_principles {{
        user_id,
        account_id,
        full,
        processed_at,
        scores,
        @ "NOW"
    }}
    """
    
    return client.run(query)


def save_results_query(user_id: UUID4, scores: dict, full_assesment: bool = False) -> DataFrame:
    query = f"""
    input[
        user_id,
        full,
        scores,
    ] <- [[
        to_uuid("{user_id}"),
        {str(full_assesment).lower()},  # true if full assessment results
        {json.dumps(scores)},  # json returned as result
    ]]

    ?[
        user_id,
        full,
        scores,
        account_id,
        processed_at,
    ] := input[
        user_id,
        full,
        scores,
    ],
        *user_principles {{
        user_id,
        account_id,
    }}, processed_at = null

    :put user_principles {{
        user_id,
        account_id,
        full,
        scores,
        processed_at,
    }}
    """
    
    return client.run(query)


def get_user_data(user_id: UUID4) -> DataFrame:
    """
    :create users {
        user_id: Uuid,
        updated_at: Validity default [floor(now()), true],
        =>
        name: String,
        email: String,
        about: String default "",
        metadata: Json default {},
        created_at: Float default now(),
    }
    """
    query = """
    input[user_id] <- [[
        to_uuid("{user_id}"),
    ]]

    ?[
        user_id,
        name,
        email,
    ] := input[user_id],
    *users {{
        user_id,
        name,
        email,
    }}
    """

    return client.run(query)


def init():
    query = """
    :create user_principles {
        user_id: Uuid,
        account_id: String,
        full: Bool default false,
        updated_at: Validity default [floor(now()), true],
        =>
        processed_at: Float? default null,
        scores: Json? default null
    }
    """
    try:
        client.run(query)
    except Exception as e:
        logger.exception(e)
