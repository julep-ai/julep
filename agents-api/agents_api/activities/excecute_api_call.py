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

    # QUESTION[@Bhabuk10]: Why is `json_` named with an underscore? Is it to avoid conflicting with 
    # a Python keyword or another variable? Adding a comment to explain this decision would 
    # improve clarity for other developers.

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
            # FEEDBACK[@Bhabuk10]: Consider adding timeout handling for the `httpx` client. 
            # Timeouts are essential for making the application resilient to network issues. 
            # You could add a timeout parameter to `AsyncClient` for better control over the request.

        response_dict = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.content,
            "json": response.json(),
        }
        # FEEDBACK[@Bhabuk10]: While this is a comprehensive response, it would be a good idea to add 
        # exception handling around `response.json()` to handle cases where the response body isn't 
        # valid JSON, which could prevent unwanted crashes in those cases.

        return response_dict

    except BaseException as e:
        if activity.in_activity():
            activity.logger.error(f"Error in execute_api_call: {e}")

        raise
        # QUESTION[@Bhabuk10]: Why is `BaseException` being caught here instead of more specific 
        # exceptions like `httpx.HTTPError`? Catching broad exceptions can make debugging harder. 
        # Consider catching more specific exceptions to handle different cases effectively.

mock_execute_api_call = execute_api_call

execute_api_call = activity.defn(name="execute_api_call")(
    execute_api_call if not testing else mock_execute_api_call
)

# FEEDBACK[@Bhabuk10]: It's great that testing is considered here with `mock_execute_api_call`. 
# It might be useful to provide more context on how `mock_execute_api_call` differs from 
# the actual `execute_api_call`, especially for new developers or contributors unfamiliar with this pattern.
