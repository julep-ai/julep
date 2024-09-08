from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_task_request import CreateTaskRequest
from ...models.resource_created_response import ResourceCreatedResponse
from ...models.tasks_route_create_accept import TasksRouteCreateAccept
from ...types import UNSET, Response


def _get_kwargs(
    id: str,
    *,
    body: CreateTaskRequest,
    accept: TasksRouteCreateAccept,
) -> Dict[str, Any]:
    headers: Dict[str, Any] = {}
    headers["accept"] = str(accept)

    _kwargs: Dict[str, Any] = {
        "method": "post",
        "url": "/agents/{id}/tasks".format(
            id=id,
        ),
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[ResourceCreatedResponse]:
    if response.status_code == HTTPStatus.OK:
        response_200 = ResourceCreatedResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[ResourceCreatedResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateTaskRequest,
    accept: TasksRouteCreateAccept,
) -> Response[ResourceCreatedResponse]:
    """Create a new task

    Args:
        id (str):
        accept (TasksRouteCreateAccept):
        body (CreateTaskRequest): Payload for creating a task

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceCreatedResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        accept=accept,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateTaskRequest,
    accept: TasksRouteCreateAccept,
) -> Optional[ResourceCreatedResponse]:
    """Create a new task

    Args:
        id (str):
        accept (TasksRouteCreateAccept):
        body (CreateTaskRequest): Payload for creating a task

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceCreatedResponse
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
        accept=accept,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateTaskRequest,
    accept: TasksRouteCreateAccept,
) -> Response[ResourceCreatedResponse]:
    """Create a new task

    Args:
        id (str):
        accept (TasksRouteCreateAccept):
        body (CreateTaskRequest): Payload for creating a task

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceCreatedResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        accept=accept,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateTaskRequest,
    accept: TasksRouteCreateAccept,
) -> Optional[ResourceCreatedResponse]:
    """Create a new task

    Args:
        id (str):
        accept (TasksRouteCreateAccept):
        body (CreateTaskRequest): Payload for creating a task

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceCreatedResponse
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
            accept=accept,
        )
    ).parsed
