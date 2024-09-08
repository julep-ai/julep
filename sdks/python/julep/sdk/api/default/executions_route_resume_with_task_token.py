from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.resource_updated_response import ResourceUpdatedResponse
from ...models.task_token_resume_execution_request import (
    TaskTokenResumeExecutionRequest,
)
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: TaskTokenResumeExecutionRequest,
    task_token: str,
) -> Dict[str, Any]:
    headers: Dict[str, Any] = {}

    params: Dict[str, Any] = {}

    params["task_token"] = task_token

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "post",
        "url": "/executions",
        "params": params,
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[ResourceUpdatedResponse]:
    if response.status_code == HTTPStatus.OK:
        response_200 = ResourceUpdatedResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[ResourceUpdatedResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: TaskTokenResumeExecutionRequest,
    task_token: str,
) -> Response[ResourceUpdatedResponse]:
    """Resume an execution with a task token

    Args:
        task_token (str):
        body (TaskTokenResumeExecutionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceUpdatedResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        task_token=task_token,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: TaskTokenResumeExecutionRequest,
    task_token: str,
) -> Optional[ResourceUpdatedResponse]:
    """Resume an execution with a task token

    Args:
        task_token (str):
        body (TaskTokenResumeExecutionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceUpdatedResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        task_token=task_token,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: TaskTokenResumeExecutionRequest,
    task_token: str,
) -> Response[ResourceUpdatedResponse]:
    """Resume an execution with a task token

    Args:
        task_token (str):
        body (TaskTokenResumeExecutionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceUpdatedResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        task_token=task_token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: TaskTokenResumeExecutionRequest,
    task_token: str,
) -> Optional[ResourceUpdatedResponse]:
    """Resume an execution with a task token

    Args:
        task_token (str):
        body (TaskTokenResumeExecutionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceUpdatedResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            task_token=task_token,
        )
    ).parsed
