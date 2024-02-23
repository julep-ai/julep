import os
import uuid
import pytest
from fastapi.testclient import TestClient
from model_api.web import create_app


MODEL = "julep-ai/samantha-1-turbo"
args = ["--model", MODEL, "--trust-remote-code", "--max-model-len", "15000"]
app = create_app(args)


@pytest.fixture(scope="session")
def unauthorized_client():
    return TestClient(app)


@pytest.fixture(scope="session")
def client():
    auth_key = "myauthkey"
    os.environ["API_KEY"] = auth_key
    # os.environ["TEMPERATURE_SCALING_FACTOR"] = "0.0"

    return TestClient(app, headers={"X-Auth-Key": auth_key})


@pytest.fixture
def request_id():
    return str(uuid.uuid4())
