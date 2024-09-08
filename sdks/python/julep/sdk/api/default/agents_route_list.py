from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.route_list_direction import RouteListDirection
from ...models.route_list_response_200 import RouteListResponse200
from ...models.route_list_sort_by import RouteListSortBy
from ...types import UNSET, Response


def _get_kwargs(
    *,
    limit: int,
    offset: int,
    sort_by: RouteListSortBy = RouteListSortBy.CREATED_AT,
    direction: RouteListDirection = RouteListDirection.ASC,
    metadata_filter: str = "{}",
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["limit"] = limit

    params["offset"] = offset

    json_sort_by = sort_by.value
    params["sort_by"] = json_sort_by

    json_direction = direction.value
    params["direction"] = json_direction

    params["metadata_filter"] = metadata_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/agents",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[RouteListResponse200]:
    if response.status_code == HTTPStatus.OK:
        response_200 = RouteListResponse200.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[RouteListResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: int,
    offset: int,
    sort_by: RouteListSortBy = RouteListSortBy.CREATED_AT,
    direction: RouteListDirection = RouteListDirection.ASC,
    metadata_filter: str = "{}",
) -> Response[RouteListResponse200]:
    """List Agents (paginated)

    Args:
        limit (int): Limit the number of results
        offset (int): Offset to apply to the results
        sort_by (RouteListSortBy):  Default: RouteListSortBy.CREATED_AT.
        direction (RouteListDirection):  Default: RouteListDirection.ASC.
        metadata_filter (str):  Default: '{}'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[RouteListResponse200]
    """

    kwargs = _get_kwargs(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: int,
    offset: int,
    sort_by: RouteListSortBy = RouteListSortBy.CREATED_AT,
    direction: RouteListDirection = RouteListDirection.ASC,
    metadata_filter: str = "{}",
) -> Optional[RouteListResponse200]:
    """List Agents (paginated)

    Args:
        limit (int): Limit the number of results
        offset (int): Offset to apply to the results
        sort_by (RouteListSortBy):  Default: RouteListSortBy.CREATED_AT.
        direction (RouteListDirection):  Default: RouteListDirection.ASC.
        metadata_filter (str):  Default: '{}'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        RouteListResponse200
    """

    return sync_detailed(
        client=client,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: int,
    offset: int,
    sort_by: RouteListSortBy = RouteListSortBy.CREATED_AT,
    direction: RouteListDirection = RouteListDirection.ASC,
    metadata_filter: str = "{}",
) -> Response[RouteListResponse200]:
    """List Agents (paginated)

    Args:
        limit (int): Limit the number of results
        offset (int): Offset to apply to the results
        sort_by (RouteListSortBy):  Default: RouteListSortBy.CREATED_AT.
        direction (RouteListDirection):  Default: RouteListDirection.ASC.
        metadata_filter (str):  Default: '{}'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[RouteListResponse200]
    """

    kwargs = _get_kwargs(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: int,
    offset: int,
    sort_by: RouteListSortBy = RouteListSortBy.CREATED_AT,
    direction: RouteListDirection = RouteListDirection.ASC,
    metadata_filter: str = "{}",
) -> Optional[RouteListResponse200]:
    """List Agents (paginated)

    Args:
        limit (int): Limit the number of results
        offset (int): Offset to apply to the results
        sort_by (RouteListSortBy):  Default: RouteListSortBy.CREATED_AT.
        direction (RouteListDirection):  Default: RouteListDirection.ASC.
        metadata_filter (str):  Default: '{}'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        RouteListResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            direction=direction,
            metadata_filter=metadata_filter,
        )
    ).parsed
