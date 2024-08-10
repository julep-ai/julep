from pycozo.client import Client

from ..env import cozo_auth, cozo_host
from ..web import app

options = {"host": cozo_host}
if cozo_auth:
    options.update({"auth": cozo_auth})


def get_cozo_client():
    client = getattr(app.state, "cozo_client", Client("http", options=options))
    if not hasattr(app.state, "cozo_client"):
        app.state.cozo_client = client

    return client
