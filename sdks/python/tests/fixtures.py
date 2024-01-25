from ward import fixture
from julep import AsyncClient, Client


@fixture(scope="global")
def client():
    # Mock server base url
    base_url = "http://localhost:8080"
    client = Client(api_key="thisisnotarealapikey", base_url=base_url)

    return client


@fixture
def async_client():
    # Mock server base url
    base_url = "http://localhost:8080"
    client = AsyncClient(api_key="thisisnotarealapikey", base_url=base_url)

    return client
