import base64
from typing import Any, TypedDict

import httpx
from beartype import beartype
from temporalio import activity

from ..autogen.openapi_model import ApiCallDef
from ..env import testing
from ..common.protocol.tasks import StepOutcome

class RequestArgs(TypedDict):
    content: str | None
    data: dict[str, Any] | None
    json_: dict[str, Any] | None
    cookies: dict[str, str] | None
    params: str | dict[str, Any] | None
    url: str | None
    headers: dict[str, str] | None


@beartype
async def execute_api_call(
    api_call: ApiCallDef,
    request_args: RequestArgs,
) -> Any:
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            arg_url = request_args.pop("url", None)
            arg_headers = request_args.pop("headers", None)

            response = await client.request(
                method=api_call.method,
                url=arg_url or str(api_call.url),
                headers={**(arg_headers or {}), **(api_call.headers or {})},
                follow_redirects=api_call.follow_redirects,
                **request_args,
            )

        response.raise_for_status()
        content_base64 = base64.b64encode(response.content).decode("ascii")

        response_dict = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": content_base64,
        }

        try:
            response_dict["json"] = response.json()
        except BaseException as e:
            response_dict["json"] = None
            activity.logger.debug(f"Failed to parse JSON response: {e}")

        return response_dict

    except BaseException as e:
        if activity.in_activity():
            activity.logger.error(f"Error in execute_api_call: {e}")

        return StepOutcome(error=str(e))


mock_execute_api_call = execute_api_call

execute_api_call = activity.defn(name="execute_api_call")(
    execute_api_call if not testing else mock_execute_api_call
)
