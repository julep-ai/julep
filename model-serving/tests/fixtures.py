import os
import uuid
import pytest
from fastapi.testclient import TestClient

auth_key = "myauthkey"
os.environ["API_KEY"] = auth_key
os.environ["TEMPERATURE_SCALING_FACTOR"] = "1.0"
os.environ["TEMPERATURE_SCALING_POWER"] = "1.0"
MODEL_NAME = os.environ.get("MODEL_NAME", "julep-ai/samantha-1-turbo")

from model_api.web import create_app  # noqa: E402

args = [
    "--model",
    MODEL_NAME,
    "--trust-remote-code",
    "--max-model-len",
    "1024",
    "--enforce-eager",
    "--dtype",
    "bfloat16",
    "--gpu-memory-utilization",
    "0.97",
    "--max-num-seqs",
    "1",
]

app = create_app(args)


@pytest.fixture(scope="session")
def unauthorized_client():
    return TestClient(app)


@pytest.fixture(scope="session")
def client():
    return TestClient(app, headers={"X-Auth-Key": auth_key})


@pytest.fixture
def request_id():
    return str(uuid.uuid4())
