from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.resource_updated_response import ResourceUpdatedResponse
from ...models.update_task_request import UpdateTaskRequest
from ...types import UNSET, Response


def _get_kwargs(
    id: str,
    child_id: str,
    *,
    body: UpdateTaskRequest,
) -> Dict[str, Any]:
    headers: Dict[str, Any] = {}

    _kwargs: Dict[str, Any] = {
        "method": "put",
        "url": "/agents/{id}/tasks/{child_id}".format(
            id=id,
            child_id=child_id,
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
    id: str,
    child_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateTaskRequest,
) -> Response[ResourceUpdatedResponse]:
    """Update an existing task (overwrite existing values)

    Args:
        id (str):
        child_id (str):
        body (UpdateTaskRequest): Payload for updating a task

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceUpdatedResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        child_id=child_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    child_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateTaskRequest,
) -> Optional[ResourceUpdatedResponse]:
    """Update an existing task (overwrite existing values)

    Args:
        id (str):
        child_id (str):
        body (UpdateTaskRequest): Payload for updating a task

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceUpdatedResponse
    """

    return sync_detailed(
        id=id,
        child_id=child_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: str,
    child_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateTaskRequest,
) -> Response[ResourceUpdatedResponse]:
    """Update an existing task (overwrite existing values)

    Args:
        id (str):
        child_id (str):
        body (UpdateTaskRequest): Payload for updating a task

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceUpdatedResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        child_id=child_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    child_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateTaskRequest,
) -> Optional[ResourceUpdatedResponse]:
    """Update an existing task (overwrite existing values)

    Args:
        id (str):
        child_id (str):
        body (UpdateTaskRequest): Payload for updating a task

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceUpdatedResponse
    """

    return (
        await asyncio_detailed(
            id=id,
            child_id=child_id,
            client=client,
            body=body,
        )
    ).parsed
