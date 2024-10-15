import base64
from typing import Any, Optional, TypedDict, Union

import httpx
from beartype import beartype
from temporalio import activity

from ..autogen.openapi_model import ApiCallDef

# from ..clients import integrations
from ..env import testing

# from ..models.tools import get_tool_args_from_metadata


class RequestArgs(TypedDict):
    content: Optional[str]
    data: Optional[dict[str, Any]]
    json_: Optional[dict[str, Any]]
    cookies: Optional[dict[str, str]]
    params: Optional[Union[str, dict[str, Any]]]
    url: Optional[str]
    headers: Optional[dict[str, str]]


@beartype
async def execute_api_call(
    api_call: ApiCallDef,
    request_args: RequestArgs,
) -> Any:
    try:
        async with httpx.AsyncClient() as client:
            arg_url = request_args.pop("url", None)
            arg_headers = request_args.pop("headers", None)

            response = await client.request(
                method=api_call.method,
                url=arg_url or str(api_call.url),
                headers=arg_headers or api_call.headers,
                follow_redirects=api_call.follow_redirects,
                **request_args,
            )

        content_base64 = base64.b64encode(response.content).decode("ascii")

        response_dict = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": content_base64,
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
