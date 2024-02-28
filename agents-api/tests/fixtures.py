from ward import fixture
from julep import AsyncClient, Client

# TODO: make clients connect to real service


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


@fixture
def agent(client=client):
    return client.agents.create(
        name="Samantha",
        about="about Samantha",
        instructions=[
            {
                "content": "non-important content",
                "important": False,
            },
            {
                "content": "important content",
                "important": True,
            },
        ],
        functions=[
            {
                "description": "func desc",
                "name": "some_func",
                "parameters": {"param1": "string"},
            }
        ],
        default_settings={
            "frequency_penalty": 0.1,
            "length_penalty": 0.9,
            "presence_penalty": 0.8,
            "repetition_penalty": 0.7,
            "temperature": 0.6,
            "top_p": 0.5,
        },
        model="julep-ai/samantha-1-turbo",
        docs=[
            {
                "title": "some titie",
                "content": "some content",
            },
        ],
    )


@fixture
def user(client=client):
    return client.users.create(
        name="test user",
        about="test user about",
    )


@fixture
def session(user=user, agent=agent, client=client):
    return client.sessions.create(
        user_id=user.id,
        agent_id=agent.id,
        situation="test situation",
    )
