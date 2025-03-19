import base64
import json
from typing import Any, TypedDict
from uuid import UUID

import httpx
from beartype import beartype
from httpx import Response
from psycopg import AsyncConnection
from temporalio import activity

from ..autogen.openapi_model import ApiCallDef
from ..common.utils.template import get_secrets, render_template
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
    conn: AsyncConnection[dict[str, Any]] | None = None,
    developer_id: UUID | None = None,
    agent_id: UUID | None = None,
) -> Any:
    """
    Execute an API call with optional secrets support.

    Args:
        api_call: The API call definition.
        request_args: The request arguments.
        conn: Optional database connection for secrets resolution.
        developer_id: Optional developer ID for secrets resolution.
        agent_id: Optional agent ID for secrets resolution.

    Returns:
        The API response data.
    """
    try:
        # Process secrets if they're provided and we have the necessary context
        processed_headers = {}

        if api_call.secrets and conn and developer_id:
            # Get secrets from the database
            secrets_dict = await get_secrets(
                conn=conn,
                developer_id=developer_id,
                agent_id=agent_id,
                secret_refs=api_call.secrets,
            )

            # Process headers with secrets
            if api_call.headers:
                for key, value in api_call.headers.items():
                    # If the header value is a string, try to render it with secrets
                    if isinstance(value, str) and "$" in value:
                        try:
                            rendered_value = await render_template(
                                value,
                                {"secrets": secrets_dict}
                            )
                            processed_headers[key] = rendered_value
                        except Exception as e:
                            activity.logger.warning(f"Failed to render header template: {e}")
                            processed_headers[key] = value
                    else:
                        processed_headers[key] = value

        # Use the processed headers if available, otherwise use the original headers
        headers_to_use = processed_headers if processed_headers else (api_call.headers or {})

        async with httpx.AsyncClient(timeout=600) as client:
            arg_headers: dict = request_args.pop("headers", None) or {}
            # Allow the method to be overridden by the request_args
            response: Response = await client.request(
                method=request_args.pop("method", api_call.method),
                url=str(request_args.pop("url", api_call.url)),
                headers={**arg_headers, **headers_to_use},
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
            except json.JSONDecodeError as e:
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
