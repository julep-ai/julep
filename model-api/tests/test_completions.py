import os
import pytest
import model_api.web
from pytest_mock import mocker
from fastapi.testclient import TestClient
from model_api.web import create_app
from model_api.protocol import CompletionRequest
from model_api.logits_processors import drop_disallowed_start_tags
from vllm.sampling_params import SamplingParams


MODEL = "Open-Orca/oo-phi-1_5"


@pytest.fixture
def unauthorized_client(args):
    return TestClient(create_app(args))


@pytest.fixture
def client(args):
    auth_key = "myauthkey"
    os.environ["API_KEY"] = auth_key
    os.environ["TEMPERATURE_SCALING_FACTOR"] = 0.0
    app = create_app(args)

    return TestClient(app, headers={"X-Auth-Key": auth_key})


@pytest.mark.parametrize("unauthorized_client", [["--model", MODEL]], indirect=True)
def test_security(unauthorized_client):
    response = unauthorized_client.post("/v1/completions")
    assert response.status_code == 403


@pytest.mark.parametrize("client", [["--model", MODEL]], indirect=True)
def test_check_model(client):
    body = CompletionRequest(
        model="some_nonexistent_model",
    ).model_dump()
    response = client.post(
        "/v1/completions",
        json=body,
    )
    assert response.status_code == 404


@pytest.mark.parametrize("client", [["--model", MODEL]], indirect=True)
def test_logit_bias_not_supported(client):
    body = CompletionRequest(
        model=MODEL,
        logit_bias={"a": 1.0},
    ).model_dump()
    response = client.post(
        "/v1/completions",
        json=body,
    )
    assert response.status_code == 400


@pytest.mark.parametrize("client", [["--model", MODEL]], indirect=True)
def test_remove_last_space(client, mocker):
    st = list(model_api.web.engine.engine.tokenizer.tokenizer.special_tokens_map.values())[0]
    if isinstance(st, list):
        st = st[0]
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>User
{st[0]} {st[1:]}<|im_end|>
<|im_start|>me """
    prompt = expected_prompt + " "
    expected_sampling_params = None
    request_id = "request_id1"

    with mocker.patch("model_api.web.random_uuid") as random_uuid:
        random_uuid.return_value = request_id
        spy = mocker.spy(model_api.web.engine, "generate")

        body = CompletionRequest(
            model=MODEL,
            prompt=prompt,
        ).model_dump()
        response = client.post(
            "/v1/completions",
            json=body,
        )
        assert spy.call_count == 1
        spy.assert_called_once_with(expected_prompt, expected_sampling_params, request_id)
        assert response.status_code == 200


@pytest.mark.parametrize("client", [["--model", MODEL]], indirect=True)
def test_remove_last_space_2(client, mocker):
    st = list(model_api.web.engine.engine.tokenizer.tokenizer.special_tokens_map.values())[0]
    if isinstance(st, list):
        st = st[0]
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>User
{st[0]} {st[1:]}<|im_end|>
<|im_start|>me """
    prompt = expected_prompt
    expected_sampling_params = None
    request_id = "request_id1"

    with mocker.patch("model_api.web.random_uuid") as random_uuid:
        random_uuid.return_value = request_id
        spy = mocker.spy(model_api.web.engine, "generate")

        body = CompletionRequest(
            model=MODEL,
            prompt=prompt,
        ).model_dump()
        response = client.post(
            "/v1/completions",
            json=body,
        )
        assert spy.call_count == 1
        spy.assert_called_once_with(expected_prompt, expected_sampling_params, request_id)
        assert response.status_code == 200


@pytest.mark.parametrize("client", [["--model", MODEL]], indirect=True)
def test_rescale_temperature(client, mocker):
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>User
hi<|im_end|>
<|im_start|>me"""
    prompt = expected_prompt
    temperature = 0.7
    expected_sampling_params = SamplingParams(temperature=0.0)
    request_id = "request_id1"

    with mocker.patch("model_api.web.random_uuid") as random_uuid:
        random_uuid.return_value = request_id
        spy = mocker.spy(model_api.web.engine, "generate")

        body = CompletionRequest(
            model=MODEL,
            temperature=temperature,
            prompt=prompt,
        ).model_dump()
        response = client.post(
            "/v1/completions",
            json=body,
        )
        assert spy.call_count == 1
        spy.assert_called_once_with(expected_prompt, expected_sampling_params, request_id)
        assert response.status_code == 200


@pytest.mark.parametrize("client", [["--model", MODEL]], indirect=True)
def test_logits_processor_drop_disallowed_start_tags(client, mocker):
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>User
hi<|im_end|>
<|im_start|>"""
    prompt = expected_prompt
    expected_sampling_params = SamplingParams(logits_processors=[drop_disallowed_start_tags])
    request_id = "request_id1"

    with mocker.patch("model_api.web.random_uuid") as random_uuid:
        random_uuid.return_value = request_id
        spy = mocker.spy(model_api.web.engine, "generate")

        body = CompletionRequest(
            model=MODEL,
            prompt=prompt,
        ).model_dump()
        response = client.post(
            "/v1/completions",
            json=body,
        )
        assert spy.call_count == 1
        spy.assert_called_once_with(expected_prompt, expected_sampling_params, request_id)
        assert response.status_code == 200
