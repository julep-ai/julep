import base64
from typing import Any, TypedDict

import httpx
from beartype import beartype
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


@beartype
async def execute_api_call(
    api_call: ApiCallDef,
    request_args: RequestArgs,
) -> Any:
    try:
        # Use client with timeout and proper error handling
        async with httpx.AsyncClient(timeout=600) as client:
            # Extract URL and headers from arguments
            arg_url = request_args.pop("url", None)
            arg_headers = request_args.pop("headers", None)

            # Merge headers from both arguments and API call definition
            merged_headers = {**(arg_headers or {}), **(api_call.headers or {})}

            # Log the request (debug level)
            if activity.in_activity():
                activity.logger.debug(
                    f"Making API call: {api_call.method} to {arg_url or str(api_call.url)}"
                )

            # Execute the HTTP request
            response = await client.request(
                method=api_call.method,
                url=arg_url or str(api_call.url),
                headers=merged_headers,
                follow_redirects=api_call.follow_redirects,
                **request_args,
            )

        # Raise for HTTP errors
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # For HTTP errors, include response body in the error for debugging
            error_body = e.response.text[:500] if e.response.text else "(empty body)"
            if activity.in_activity():
                activity.logger.error(
                    f"HTTP error {e.response.status_code} in API call: {e!s}\n"
                    f"Response body: {error_body}"
                )
            raise

        # Encode content as base64 for safety
        content_base64 = base64.b64encode(response.content).decode("ascii")

        # Prepare response dictionary
        response_dict = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": content_base64,
        }

        # Try to parse JSON response if possible
        try:
            response_dict["json"] = response.json()
        except Exception as e:
            response_dict["json"] = None
            content_preview = response.text[:100] if response.text else "(empty)"
            if activity.in_activity():
                activity.logger.debug(
                    f"Response not valid JSON: {e!s}\n"
                    f"Content-Type: {response.headers.get('content-type')}\n"
                    f"Content preview: {content_preview}"
                )

        return response_dict

    except httpx.TimeoutException as e:
        if activity.in_activity():
            activity.logger.error(f"Timeout in API call: {e!s}")
        raise
    except httpx.RequestError as e:
        # Network-level errors
        if activity.in_activity():
            activity.logger.error(f"Request error in API call: {e!s}")
        raise
    except Exception as e:
        if activity.in_activity():
            activity.logger.error(f"Error in execute_api_call: {e!s}")
        raise


mock_execute_api_call = execute_api_call

execute_api_call = activity.defn(name="execute_api_call")(
    execute_api_call if not testing else mock_execute_api_call,
)
