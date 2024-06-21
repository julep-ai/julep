#!/usr/bin/env python3

"""This module provides utility functions for interacting with the Cozo API client, including data mutation processes."""

from types import SimpleNamespace
from uuid import UUID

from pycozo import Client

# Define a mock client for testing purposes, simulating Cozo API client behavior.
_fake_client = SimpleNamespace()
# Lambda function to process and mutate data dictionaries using the Cozo client's internal method. This is a workaround to access protected member functions for testing.
_fake_client._process_mutate_data_dict = lambda data: (
    Client._process_mutate_data_dict(_fake_client, data)
)

# Public interface to process and mutate data using the Cozo client. It wraps the client's internal processing method for external use.
cozo_process_mutate_data = _fake_client._process_mutate_data = lambda data: (
    Client._process_mutate_data(_fake_client, data)
)

uuid_int_list_to_uuid4 = lambda data: UUID(
    bytes=b"".join([i.to_bytes(1, "big") for i in data])
)
