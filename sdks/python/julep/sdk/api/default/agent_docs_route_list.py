from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.agent_docs_route_list_direction import AgentDocsRouteListDirection
from ...models.agent_docs_route_list_response_200 import AgentDocsRouteListResponse200
from ...models.agent_docs_route_list_sort_by import AgentDocsRouteListSortBy
from ...types import UNSET, Response


def _get_kwargs(
    id: str,
    *,
    limit: int,
    offset: int,
    sort_by: AgentDocsRouteListSortBy = AgentDocsRouteListSortBy.CREATED_AT,
    direction: AgentDocsRouteListDirection = AgentDocsRouteListDirection.ASC,
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
        "url": "/agents/{id}/docs".format(
            id=id,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[AgentDocsRouteListResponse200]:
    if response.status_code == HTTPStatus.OK:
        response_200 = AgentDocsRouteListResponse200.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[AgentDocsRouteListResponse200]:
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
    limit: int,
    offset: int,
    sort_by: AgentDocsRouteListSortBy = AgentDocsRouteListSortBy.CREATED_AT,
    direction: AgentDocsRouteListDirection = AgentDocsRouteListDirection.ASC,
    metadata_filter: str = "{}",
) -> Response[AgentDocsRouteListResponse200]:
    """List Docs owned by an Agent

    Args:
        id (str):
        limit (int): Limit the number of results
        offset (int): Offset to apply to the results
        sort_by (AgentDocsRouteListSortBy):  Default: AgentDocsRouteListSortBy.CREATED_AT.
        direction (AgentDocsRouteListDirection):  Default: AgentDocsRouteListDirection.ASC.
        metadata_filter (str):  Default: '{}'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentDocsRouteListResponse200]
    """

    kwargs = _get_kwargs(
        id=id,
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
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    limit: int,
    offset: int,
    sort_by: AgentDocsRouteListSortBy = AgentDocsRouteListSortBy.CREATED_AT,
    direction: AgentDocsRouteListDirection = AgentDocsRouteListDirection.ASC,
    metadata_filter: str = "{}",
) -> Optional[AgentDocsRouteListResponse200]:
    """List Docs owned by an Agent

    Args:
        id (str):
        limit (int): Limit the number of results
        offset (int): Offset to apply to the results
        sort_by (AgentDocsRouteListSortBy):  Default: AgentDocsRouteListSortBy.CREATED_AT.
        direction (AgentDocsRouteListDirection):  Default: AgentDocsRouteListDirection.ASC.
        metadata_filter (str):  Default: '{}'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentDocsRouteListResponse200
    """

    return sync_detailed(
        id=id,
        client=client,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    limit: int,
    offset: int,
    sort_by: AgentDocsRouteListSortBy = AgentDocsRouteListSortBy.CREATED_AT,
    direction: AgentDocsRouteListDirection = AgentDocsRouteListDirection.ASC,
    metadata_filter: str = "{}",
) -> Response[AgentDocsRouteListResponse200]:
    """List Docs owned by an Agent

    Args:
        id (str):
        limit (int): Limit the number of results
        offset (int): Offset to apply to the results
        sort_by (AgentDocsRouteListSortBy):  Default: AgentDocsRouteListSortBy.CREATED_AT.
        direction (AgentDocsRouteListDirection):  Default: AgentDocsRouteListDirection.ASC.
        metadata_filter (str):  Default: '{}'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentDocsRouteListResponse200]
    """

    kwargs = _get_kwargs(
        id=id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    limit: int,
    offset: int,
    sort_by: AgentDocsRouteListSortBy = AgentDocsRouteListSortBy.CREATED_AT,
    direction: AgentDocsRouteListDirection = AgentDocsRouteListDirection.ASC,
    metadata_filter: str = "{}",
) -> Optional[AgentDocsRouteListResponse200]:
    """List Docs owned by an Agent

    Args:
        id (str):
        limit (int): Limit the number of results
        offset (int): Offset to apply to the results
        sort_by (AgentDocsRouteListSortBy):  Default: AgentDocsRouteListSortBy.CREATED_AT.
        direction (AgentDocsRouteListDirection):  Default: AgentDocsRouteListDirection.ASC.
        metadata_filter (str):  Default: '{}'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentDocsRouteListResponse200
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            direction=direction,
            metadata_filter=metadata_filter,
        )
    ).parsed
