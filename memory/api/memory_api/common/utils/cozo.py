#!/usr/bin/env python3

from types import SimpleNamespace

from pycozo import Client

_fake_client = SimpleNamespace()
_fake_client._process_mutate_data_dict = lambda data: (
    Client._process_mutate_data_dict(_fake_client, data)
)

cozo_process_mutate_data = _fake_client._process_mutate_data = lambda data: (
    Client._process_mutate_data(_fake_client, data)
)
