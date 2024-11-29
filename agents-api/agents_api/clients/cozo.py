from typing import Dict

from pycozo.client import Client
from pycozo_async import Client as AsyncClient

from ..env import cozo_auth, cozo_host
from ..web import app

options: Dict[str, str] = {"host": cozo_host}
if cozo_auth:
    options.update({"auth": cozo_auth})


def get_cozo_client() -> Client:
    client = getattr(app.state, "cozo_client", Client("http", options=options))
    if not hasattr(app.state, "cozo_client"):
        app.state.cozo_client = client

    return client


def get_async_cozo_client() -> AsyncClient:
    client = getattr(
        app.state, "async_cozo_client", AsyncClient("http", options=options)
    )
    if not hasattr(app.state, "async_cozo_client"):
        app.state.async_cozo_client = client

    return client
