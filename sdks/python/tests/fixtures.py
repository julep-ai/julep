from typing import Optional

from environs import Env
from ward import fixture

from julep import AsyncClient, Client

env = Env()

TEST_API_KEY: Optional[str] = env.str("TEST_API_KEY", "thisisnotarealapikey")
TEST_API_URL: Optional[str] = env.str("TEST_API_URL", "http://localhost:8080/api")


@fixture(scope="global")
def client():
    client = Client(
        api_key=TEST_API_KEY,
        base_url=TEST_API_URL,
    )

    return client


@fixture
def async_client():
    client = AsyncClient(
        api_key=TEST_API_KEY,
        base_url=TEST_API_URL,
    )

    return client
