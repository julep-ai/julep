import base64
from typing import Any, TypedDict

import httpx
from beartype import beartype
from httpx import Response
from temporalio import activity

from ..autogen.openapi_model import ApiCallDef
from ..env import testing


class RequestArgs(TypedDict):
    content: str | None
    data: dict[str, Any] | None
    json_: dict[str, Any] | None
    cookies: dict[str, str] | None
    params: str | dict[str, Any] | None
    url: str | None
    headers: dict[str, str] | None
    files: dict[str, Any] | None
    method: str | None
    follow_redirects: bool | None


@beartype
async def execute_api_call(
    api_call: ApiCallDef,
    request_args: RequestArgs,
) -> Any:
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            arg_headers: dict = request_args.pop("headers", None) or {}
            # Allow the method to be overridden by the request_args
            response: Response = await client.request(
                method=request_args.pop("method", api_call.method),
                url=str(request_args.pop("url", api_call.url)),
                headers={**arg_headers, **(api_call.headers or {})},
                follow_redirects=request_args.pop(
                    "follow_redirects", api_call.follow_redirects
                ),
                **request_args,
            )
            # Raise an error if the response is not successful
            response.raise_for_status()
            # Get the content of the response
            content_base64 = base64.b64encode(response.content).decode("ascii")
            #  Create a response dict with the status code, headers, and content
            response_dict = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": content_base64,
            }
            # Try to parse the response as JSON
            try:
                response_dict["json"] = response.json()
            except (httpx.HTTPError, httpx.StreamError) as e:
                response_dict["json"] = None
                activity.logger.debug(f"Failed to parse JSON response: {e}")

        return response_dict

    except BaseException as e:
        if activity.in_activity():
            activity.logger.error(f"Error in execute_api_call: {e}")

        raise


mock_execute_api_call = execute_api_call

execute_api_call = activity.defn(name="execute_api_call")(
    execute_api_call if not testing else mock_execute_api_call,
)
