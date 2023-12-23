from pycozo.client import Client
from ..env import cozo_host, cozo_auth


options = {"host": cozo_host}
if cozo_auth:
    options.update({"auth": cozo_auth})

client = Client("http", options=options)
