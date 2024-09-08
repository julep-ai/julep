from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_task_request import CreateTaskRequest
from ...models.resource_updated_response import ResourceUpdatedResponse
from ...models.tasks_create_or_update_route_create_or_update_accept import (
    TasksCreateOrUpdateRouteCreateOrUpdateAccept,
)
from ...types import UNSET, Response


def _get_kwargs(
    parent_id: str,
    id: str,
    *,
    body: CreateTaskRequest,
    accept: TasksCreateOrUpdateRouteCreateOrUpdateAccept,
) -> Dict[str, Any]:
    headers: Dict[str, Any] = {}
    headers["accept"] = str(accept)

    _kwargs: Dict[str, Any] = {
        "method": "post",
        "url": "/agents/{parent_id}/tasks/{id}".format(
            parent_id=parent_id,
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
) -> Optional[ResourceUpdatedResponse]:
    if response.status_code == HTTPStatus.CREATED:
        response_201 = ResourceUpdatedResponse.from_dict(response.json())

        return response_201
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
    parent_id: str,
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateTaskRequest,
    accept: TasksCreateOrUpdateRouteCreateOrUpdateAccept,
) -> Response[ResourceUpdatedResponse]:
    """Create or update a task

    Args:
        parent_id (str):
        id (str):
        accept (TasksCreateOrUpdateRouteCreateOrUpdateAccept):
        body (CreateTaskRequest): Payload for creating a task

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceUpdatedResponse]
    """

    kwargs = _get_kwargs(
        parent_id=parent_id,
        id=id,
        body=body,
        accept=accept,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_id: str,
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateTaskRequest,
    accept: TasksCreateOrUpdateRouteCreateOrUpdateAccept,
) -> Optional[ResourceUpdatedResponse]:
    """Create or update a task

    Args:
        parent_id (str):
        id (str):
        accept (TasksCreateOrUpdateRouteCreateOrUpdateAccept):
        body (CreateTaskRequest): Payload for creating a task

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceUpdatedResponse
    """

    return sync_detailed(
        parent_id=parent_id,
        id=id,
        client=client,
        body=body,
        accept=accept,
    ).parsed


async def asyncio_detailed(
    parent_id: str,
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateTaskRequest,
    accept: TasksCreateOrUpdateRouteCreateOrUpdateAccept,
) -> Response[ResourceUpdatedResponse]:
    """Create or update a task

    Args:
        parent_id (str):
        id (str):
        accept (TasksCreateOrUpdateRouteCreateOrUpdateAccept):
        body (CreateTaskRequest): Payload for creating a task

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceUpdatedResponse]
    """

    kwargs = _get_kwargs(
        parent_id=parent_id,
        id=id,
        body=body,
        accept=accept,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_id: str,
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateTaskRequest,
    accept: TasksCreateOrUpdateRouteCreateOrUpdateAccept,
) -> Optional[ResourceUpdatedResponse]:
    """Create or update a task

    Args:
        parent_id (str):
        id (str):
        accept (TasksCreateOrUpdateRouteCreateOrUpdateAccept):
        body (CreateTaskRequest): Payload for creating a task

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceUpdatedResponse
    """

    return (
        await asyncio_detailed(
            parent_id=parent_id,
            id=id,
            client=client,
            body=body,
            accept=accept,
        )
    ).parsed
