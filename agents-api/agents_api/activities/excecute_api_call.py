from typing import Annotated, Any, Optional, Union

import httpx
from beartype import beartype
from pydantic import Field
from temporalio import activity

from ..autogen.openapi_model import ApiCallDef

# from ..clients import integrations
from ..common.protocol.tasks import StepContext
from ..env import testing

# from ..models.tools import get_tool_args_from_metadata


@beartype
async def execute_api_call(
    context: StepContext,
    tool_name: str,
    api_call: ApiCallDef,
    content: Optional[str] = None,
    data: Optional[dict[str, Any]] = None,
    json_: Annotated[Optional[dict[str, Any]], Field(None, alias="json")] = None,
    cookies: Optional[dict[str, str]] = None,
    params: Optional[Union[str, dict[str, Any]]] = None,
) -> Any:
    developer_id = context.execution_input.developer_id
    agent_id = context.execution_input.agent.id
    task_id = context.execution_input.task.id

    # TODO: Implement get_tool_args_from_metadata to get the arguments and setup for the api call
    # merged_tool_setup = get_tool_args_from_metadata(
    #     developer_id=developer_id, agent_id=agent_id, task_id=task_id, arg_type="setup"
    # )

    # arguments = (
    #     merged_tool_args.get(tool_name, {}) | (integration.arguments or {}) | arguments
    # )

    try:
        return await httpx.request(
            method=api_call.method,
            url=api_call.url,
            headers=api_call.headers,
            content=content,
            data=data,
            json=json_,
            cookies=cookies,
            params=params,
            follow_redirects=api_call.follow_redirects,
        )

    except BaseException as e:
        if activity.in_activity():
            activity.logger.error(f"Error in execute_api_call: {e}")

        raise


mock_execute_api_call = execute_api_call

execute_api_call = activity.defn(name="execute_api_call")(
    execute_api_call if not testing else mock_execute_api_call
)
