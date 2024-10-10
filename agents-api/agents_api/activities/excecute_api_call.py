from typing import Annotated, Any, Optional, TypedDict, Union

import httpx
from beartype import beartype
from pydantic import Field
from temporalio import activity

from ..autogen.openapi_model import ApiCallDef

# from ..clients import integrations
from ..common.protocol.tasks import StepContext
from ..env import testing

# from ..models.tools import get_tool_args_from_metadata


class RequestArgs(TypedDict):
    content: Optional[str]
    data: Optional[dict[str, Any]]
    json_: Optional[dict[str, Any]]
    cookies: Optional[dict[str, str]]
    params: Optional[Union[str, dict[str, Any]]]


@beartype
async def execute_api_call(
    api_call: ApiCallDef,
    request_args: RequestArgs,
) -> Any:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=api_call.method,
                url=str(api_call.url),
                headers=api_call.headers,
                follow_redirects=api_call.follow_redirects,
                **request_args,
            )

        response_dict = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.content,
            "json": response.json(),
        }

        return response_dict

    except BaseException as e:
        if activity.in_activity():
            activity.logger.error(f"Error in execute_api_call: {e}")

        raise


mock_execute_api_call = execute_api_call

execute_api_call = activity.defn(name="execute_api_call")(
    execute_api_call if not testing else mock_execute_api_call
)
