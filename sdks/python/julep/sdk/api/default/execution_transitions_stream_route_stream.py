from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.transition_event import TransitionEvent
from ...types import UNSET, Response


def _get_kwargs(
    id: str,
    *,
    next_token: Union[None, str],
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    json_next_token: Union[None, str]
    json_next_token = next_token
    params["next_token"] = json_next_token

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/executions/{id}/transitions.stream".format(
            id=id,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[TransitionEvent]:
    if response.status_code == HTTPStatus.OK:
        response_200 = TransitionEvent.from_dict(response.text)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[TransitionEvent]:
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
    next_token: Union[None, str],
) -> Response[TransitionEvent]:
    """Stream events emitted by the given execution

    Args:
        id (str):
        next_token (Union[None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TransitionEvent]
    """

    kwargs = _get_kwargs(
        id=id,
        next_token=next_token,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    next_token: Union[None, str],
) -> Optional[TransitionEvent]:
    """Stream events emitted by the given execution

    Args:
        id (str):
        next_token (Union[None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TransitionEvent
    """

    return sync_detailed(
        id=id,
        client=client,
        next_token=next_token,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    next_token: Union[None, str],
) -> Response[TransitionEvent]:
    """Stream events emitted by the given execution

    Args:
        id (str):
        next_token (Union[None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TransitionEvent]
    """

    kwargs = _get_kwargs(
        id=id,
        next_token=next_token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    next_token: Union[None, str],
) -> Optional[TransitionEvent]:
    """Stream events emitted by the given execution

    Args:
        id (str):
        next_token (Union[None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TransitionEvent
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            next_token=next_token,
        )
    ).parsed
