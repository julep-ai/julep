from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.resource_deleted_response import ResourceDeletedResponse
from ...types import UNSET, Response


def _get_kwargs(
    id: str,
    child_id: str,
) -> Dict[str, Any]:
    _kwargs: Dict[str, Any] = {
        "method": "delete",
        "url": "/agents/{id}/tools/{child_id}".format(
            id=id,
            child_id=child_id,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[ResourceDeletedResponse]:
    if response.status_code == HTTPStatus.ACCEPTED:
        response_202 = ResourceDeletedResponse.from_dict(response.json())

        return response_202
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[ResourceDeletedResponse]:
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
) -> Response[ResourceDeletedResponse]:
    """Delete an existing tool by id

    Args:
        id (str):
        child_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceDeletedResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        child_id=child_id,
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
) -> Optional[ResourceDeletedResponse]:
    """Delete an existing tool by id

    Args:
        id (str):
        child_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceDeletedResponse
    """

    return sync_detailed(
        id=id,
        child_id=child_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: str,
    child_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[ResourceDeletedResponse]:
    """Delete an existing tool by id

    Args:
        id (str):
        child_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceDeletedResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        child_id=child_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    child_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[ResourceDeletedResponse]:
    """Delete an existing tool by id

    Args:
        id (str):
        child_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceDeletedResponse
    """

    return (
        await asyncio_detailed(
            id=id,
            child_id=child_id,
            client=client,
        )
    ).parsed
