import os
import pytest
import model_api.web
from pytest_mock import mocker
from fastapi.testclient import TestClient
from model_api.web import create_app
from model_api.protocol import ChatCompletionRequest
from model_api.logits_processors import drop_disallowed_start_tags, fix_function_call_prediction
from vllm.sampling_params import SamplingParams


MODEL = "microsoft/phi-2"


@pytest.fixture(scope="module")
def args():
    return ["--model", MODEL, "--trust-remote-code"]


@pytest.fixture(scope="module")
def unauthorized_client(args):
    return TestClient(create_app(args))


@pytest.fixture(scope="module")
def client(args):
    auth_key = "myauthkey"
    os.environ["API_KEY"] = auth_key
    os.environ["TEMPERATURE_SCALING_FACTOR"] = "0.0"
    app = create_app(args)

    return TestClient(app, headers={"X-Auth-Key": auth_key})


def test_security(self, unauthorized_client):
    response = unauthorized_client.post("/v1/chat/completions")
    assert response.status_code == 403


def test_check_model(client):
    body = ChatCompletionRequest(
        model="some_nonexistent_model",
        messages=[],
    ).model_dump()
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert response.status_code == 404


def test_logit_bias_not_supported(client):
    body = ChatCompletionRequest(
        model=MODEL,
        logit_bias={"a": 1.0},
        messages=[],
    ).model_dump()
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert response.status_code == 400


def test_functions_and_tools(client):
    body = ChatCompletionRequest(
        model=MODEL,
        functions=[
            {
                "name": "func_name",
                "description": "func_desc",
                "parameters": {
                    "param1": "string",
                },
            },
        ],
        tools=[
            {
                "type": "function",
                "id": "tool-1",
                "function": {
                    "name": "func_name",
                    "description": "func_desc",
                    "parameters": {
                        "param1": "string",
                    },
                },
            }
        ],
        messages=[],
    ).model_dump()
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert response.status_code == 400


def test_insert_default_situation(client, mocker):
    expected_prompt = """<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
    """
    expected_sampling_params = None
    request_id = "request_id1"

    with mocker.patch("model_api.web.random_uuid") as random_uuid:
        random_uuid.return_value = request_id
        spy = mocker.spy(model_api.web.engine, "generate")
        body = ChatCompletionRequest(
            model=MODEL,
            messages=[],
        ).model_dump()
        response = client.post(
            "/v1/chat/completions",
            json=body,
        )
        assert spy.call_count == 1
        spy.assert_called_once_with(expected_prompt, expected_sampling_params, request_id)
        assert response.status_code == 200


def test_escape_special_tokens(client, mocker):
    st = list(model_api.web.engine.engine.tokenizer.tokenizer.special_tokens_map.values())[0]
    if isinstance(st, list):
        st = st[0]
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>User
{st[0]} {st[1:]}<|im_end|>
<|im_start|>me"""
    expected_sampling_params = None
    request_id = "request_id1"

    with mocker.patch("model_api.web.random_uuid") as random_uuid:
        random_uuid.return_value = request_id
        spy = mocker.spy(model_api.web.engine, "generate")

        body = ChatCompletionRequest(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "name": "User",
                    "content": st,
                }
            ],
        ).model_dump()
        response = client.post(
            "/v1/chat/completions",
            json=body,
        )
        assert spy.call_count == 1
        spy.assert_called_once_with(expected_prompt, expected_sampling_params, request_id)
        assert response.status_code == 200


def test_function_called_by_name(client, mocker):
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>functions
Available functions:
{{
"name": "func_name",
"description": "func_desc",
"parameters": {{
    "param1": "string",
}},
}}<|im_end|>
<|im_start|>User
hi<|im_end|>
<|im_start|>function_call {{"name": "func_name",
"""
    expected_sampling_params = None
    request_id = "request_id1"

    with mocker.patch("model_api.web.random_uuid") as random_uuid:
        random_uuid.return_value = request_id
        spy = mocker.spy(model_api.web.engine, "generate")

        body = ChatCompletionRequest(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "name": "User",
                    "content": "hi",
                }
            ],
            functions=[
                {
                    "name": "func_name",
                    "description": "func_desc",
                    "parameters": {
                        "param1": "string",
                    },
                },
            ],
            function_call={"name": "func_name"},
        ).model_dump()
        response = client.post(
            "/v1/chat/completions",
            json=body,
        )
        assert spy.call_count == 1
        spy.assert_called_once_with(expected_prompt, expected_sampling_params, request_id)
        assert response.status_code == 200


def test_function_is_none(client, mocker):
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>User
hi<|im_end|>
<|im_start|>me"""
    expected_sampling_params = None
    request_id = "request_id1"

    with mocker.patch("model_api.web.random_uuid") as random_uuid:
        random_uuid.return_value = request_id
        spy = mocker.spy(model_api.web.engine, "generate")

        body = ChatCompletionRequest(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "name": "User",
                    "content": "hi",
                }
            ],
            functions=[
                {
                    "name": "func_name",
                    "description": "func_desc",
                    "parameters": {
                        "param1": "string",
                    },
                },
            ],
            function_call="none",
        ).model_dump()
        response = client.post(
            "/v1/chat/completions",
            json=body,
        )
        assert spy.call_count == 1
        spy.assert_called_once_with(expected_prompt, expected_sampling_params, request_id)
        assert response.status_code == 200


def test_function_is_auto(client, mocker):
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>functions
Available functions:
{{
"name": "func_name",
"description": "func_desc",
"parameters": {{
    "param1": "string",
}},
}}<|im_end|>
<|im_start|>User
hi<|im_end|>
<|im_start|>"""
    expected_sampling_params = None
    request_id = "request_id1"

    with mocker.patch("model_api.web.random_uuid") as random_uuid:
        random_uuid.return_value = request_id
        spy = mocker.spy(model_api.web.engine, "generate")

        body = ChatCompletionRequest(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "name": "User",
                    "content": "hi",
                }
            ],
            functions=[
                {
                    "name": "func_name",
                    "description": "func_desc",
                    "parameters": {
                        "param1": "string",
                    },
                },
            ],
            function_call="auto",
        ).model_dump()
        response = client.post(
            "/v1/chat/completions",
            json=body,
        )
        assert spy.call_count == 1
        spy.assert_called_once_with(expected_prompt, expected_sampling_params, request_id)
        assert response.status_code == 200


def test_rescale_temperature(client, mocker):
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>User
hi<|im_end|>
<|im_start|>me"""
    temperature = 0.7
    expected_sampling_params = SamplingParams(temperature=0.0)
    request_id = "request_id1"

    with mocker.patch("model_api.web.random_uuid") as random_uuid:
        random_uuid.return_value = request_id
        spy = mocker.spy(model_api.web.engine, "generate")

        body = ChatCompletionRequest(
            model=MODEL,
            temperature=temperature,
            messages=[
                {
                    "role": "user",
                    "name": "User",
                    "content": "hi",
                }
            ],
        ).model_dump()
        response = client.post(
            "/v1/chat/completions",
            json=body,
        )
        assert spy.call_count == 1
        spy.assert_called_once_with(expected_prompt, expected_sampling_params, request_id)
        assert response.status_code == 200


def test_logits_processor_fix_function_call_prediction(client, mocker):
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>functions
Available functions:
{{
"name": "func_name",
"description": "func_desc",
"parameters": {{
    "param1": "string",
}},
}}<|im_end|>
<|im_start|>User
hi<|im_end|>
<|im_start|>"""
    expected_sampling_params = SamplingParams(logits_processors=[fix_function_call_prediction])
    request_id = "request_id1"

    with mocker.patch("model_api.web.random_uuid") as random_uuid:
        random_uuid.return_value = request_id
        spy = mocker.spy(model_api.web.engine, "generate")

        body = ChatCompletionRequest(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "name": "User",
                    "content": "hi",
                }
            ],
            functions=[
                {
                    "name": "func_name",
                    "description": "func_desc",
                    "parameters": {
                        "param1": "string",
                    },
                },
            ],
            function_call="auto",
        ).model_dump()
        response = client.post(
            "/v1/chat/completions",
            json=body,
        )
        assert spy.call_count == 1
        spy.assert_called_once_with(expected_prompt, expected_sampling_params, request_id)
        assert response.status_code == 200


def test_logits_processor_drop_disallowed_start_tags(client, mocker):
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>User
hi<|im_end|>
<|im_start|>"""
    expected_sampling_params = SamplingParams(logits_processors=[drop_disallowed_start_tags])
    request_id = "request_id1"

    with mocker.patch("model_api.web.random_uuid") as random_uuid:
        random_uuid.return_value = request_id
        spy = mocker.spy(model_api.web.engine, "generate")

        body = ChatCompletionRequest(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "name": "User",
                    "content": "hi",
                }
            ],
            functions=[
                {
                    "name": "func_name",
                    "description": "func_desc",
                    "parameters": {
                        "param1": "string",
                    },
                },
            ],
            function_call="none",
        ).model_dump()
        response = client.post(
            "/v1/chat/completions",
            json=body,
        )
        assert spy.call_count == 1
        spy.assert_called_once_with(expected_prompt, expected_sampling_params, request_id)
        assert response.status_code == 200
