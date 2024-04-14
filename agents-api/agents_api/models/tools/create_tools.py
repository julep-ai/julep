from uuid import uuid4, UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...autogen.openapi_model import FunctionDef
from ...clients.cozo import client
from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow


def create_function_query(
    agent_id: UUID,
    id: UUID,
    function: FunctionDef,
    client: CozoClient = client,
) -> pd.DataFrame:
    created_at = utcnow().timestamp()

    # Process function definitions
    function = function.model_dump()

    function_data = {
        "agent_id": str(agent_id),
        "tool_id": str(id),
        "created_at": created_at,
        "name": function["name"],
        "description": function["description"],
        "parameters": function.get("parameters", {}),
    }

    function_cols, function_rows = cozo_process_mutate_data(function_data)

    query = f"""
    {{
        # Create functions
        ?[{function_cols}] <- $function_rows

        :insert agent_functions {{
            {function_cols}
        }}
        :returning
    }}"""

    return client.run(query, {"function_rows": function_rows})


def create_multiple_functions_query(
    agent_id: UUID,
    functions: list[FunctionDef],
    client: CozoClient = client,
) -> pd.DataFrame:
    agent_id = str(agent_id)
    created_at = utcnow().timestamp()

    # Process function definitions
    functions = [fn.model_dump() for fn in functions]

    function_cols, function_rows = "", []

    for function in functions:
        function_data = {
            "agent_id": agent_id,
            "created_at": created_at,
            "tool_id": str(uuid4()),
            "name": function["name"],
            "description": function["description"],
            "parameters": function["parameters"],
        }

        function_cols, new_function_rows = cozo_process_mutate_data(function_data)
        function_rows += new_function_rows

    query = f"""
    {{
        # Create functions
        ?[{function_cols}] <- $function_rows

        :insert agent_functions {{
            {function_cols}
        }}
        :returning
    }}"""

    return client.run(query, {"function_rows": function_rows})
