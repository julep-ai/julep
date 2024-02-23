import model_api.web
from pytest_mock import mocker
from model_api.logits_processors import (
    drop_disallowed_start_tags,
    fix_function_call_prediction,
)
from vllm.sampling_params import SamplingParams
from tests.fixtures import client, unauthorized_client, request_id, MODEL


def test_security(unauthorized_client):
    response = unauthorized_client.post("/v1/chat/completions")
    assert response.status_code == 403


def test_check_model(client):
    body = dict(
        model="some_nonexistent_model",
        messages=[],
    )
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert response.status_code == 404


def test_logit_bias_not_supported(client):
    body = dict(
        model=MODEL,
        logit_bias={"a": 1.0},
        messages=[],
    )
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert response.status_code == 400


def test_functions_and_tools(client):
    body = dict(
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
    )
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert response.status_code == 400


def test_do_not_insert_default_situation_if_messages_empty(client, request_id, mocker):
    expected_prompt = ""
    expected_sampling_params = SamplingParams(
        n=1,
        best_of=1,
        presence_penalty=0.0,
        frequency_penalty=0.75,
        repetition_penalty=1.0,
        temperature=0.75,
        top_p=0.99,
        top_k=-1,
        min_p=0.01,
        seed=None,
        use_beam_search=False,
        length_penalty=1.0,
        early_stopping=False,
        stop=["<", "<|"],
        stop_token_ids=[],
        include_stop_str_in_output=False,
        ignore_eos=False,
        max_tokens=1,
        logprobs=None,
        prompt_logprobs=None,
        skip_special_tokens=True,
        spaces_between_special_tokens=False,
    )

    mocker.patch("model_api.web.random_uuid", return_value=request_id)
    spy = mocker.spy(model_api.web.engine, "generate")
    body = dict(
        model=MODEL,
        messages=[],
        max_tokens=1,
        stop=["<", "<|"],
        temperature=0.75,
        frequency_penalty=0.75,
    )
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert spy.call_count == 1
    spy.assert_called_once_with(expected_prompt, expected_sampling_params, f"cmpl-{request_id}")
    assert response.status_code == 200


def test_insert_default_situation(client, request_id, mocker):
    expected_prompt = """<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>person (User)
hi<|im_end|>
<|im_start|>me"""
    expected_sampling_params = SamplingParams(
        n=1,
        best_of=1,
        presence_penalty=0.0,
        frequency_penalty=0.75,
        repetition_penalty=1.0,
        temperature=0.75,
        top_p=0.99,
        top_k=-1,
        min_p=0.01,
        seed=None,
        use_beam_search=False,
        length_penalty=1.0,
        early_stopping=False,
        stop=["<", "<|"],
        stop_token_ids=[],
        include_stop_str_in_output=False,
        ignore_eos=False,
        max_tokens=1,
        logprobs=None,
        prompt_logprobs=None,
        skip_special_tokens=True,
        spaces_between_special_tokens=False,
    )

    mocker.patch("model_api.web.random_uuid", return_value=request_id)
    spy = mocker.spy(model_api.web.engine, "generate")
    body = dict(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "name": "User",
                "content": "hi",
            }
        ],
        max_tokens=1,
        stop=["<", "<|"],
        temperature=0.75,
        frequency_penalty=0.75,
    )
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert spy.call_count == 1
    spy.assert_called_once_with(
        expected_prompt, expected_sampling_params, f"cmpl-{request_id}"
    )
    assert response.status_code == 200


def test_escape_special_tokens(client, request_id, mocker):
    st = list(
        model_api.web.engine.engine.tokenizer.tokenizer.special_tokens_map.values()
    )[0]
    if isinstance(st, list):
        st = st[0]
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>person (User)
{st[0]} {st[1:]}<|im_end|>
<|im_start|>me"""
    expected_sampling_params = SamplingParams(
        n=1,
        best_of=1,
        presence_penalty=0.0,
        frequency_penalty=0.75,
        repetition_penalty=1.0,
        temperature=0.75,
        top_p=0.99,
        top_k=-1,
        min_p=0.01,
        seed=None,
        use_beam_search=False,
        length_penalty=1.0,
        early_stopping=False,
        stop=["<", "<|"],
        stop_token_ids=[],
        include_stop_str_in_output=False,
        ignore_eos=False,
        max_tokens=1,
        logprobs=None,
        prompt_logprobs=None,
        skip_special_tokens=True,
        spaces_between_special_tokens=False,
    )

    mocker.patch("model_api.web.random_uuid", return_value=request_id)
    spy = mocker.spy(model_api.web.engine, "generate")

    body = dict(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "name": "User",
                "content": st,
            }
        ],
        max_tokens=1,
        stop=["<", "<|"],
        temperature=0.75,
        frequency_penalty=0.75,
    )
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert spy.call_count == 1
    spy.assert_called_once_with(
        expected_prompt, expected_sampling_params, f"cmpl-{request_id}"
    )
    assert response.status_code == 200


def test_function_called_by_name(client, request_id, mocker):
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
<|im_start|>person (User)
hi<|im_end|>
<|im_start|>function_call {{"name": "func_name", """
    expected_sampling_params = SamplingParams(
        n=1,
        best_of=1,
        presence_penalty=0.0,
        frequency_penalty=0.75,
        repetition_penalty=1.0,
        temperature=0.75,
        top_p=0.99,
        top_k=-1,
        min_p=0.01,
        seed=None,
        use_beam_search=False,
        length_penalty=1.0,
        early_stopping=False,
        stop=["<", "<|"],
        stop_token_ids=[],
        include_stop_str_in_output=False,
        ignore_eos=False,
        max_tokens=1,
        logprobs=None,
        prompt_logprobs=None,
        skip_special_tokens=True,
        spaces_between_special_tokens=False,
    )

    mocker.patch("model_api.web.random_uuid", return_value=request_id)
    spy = mocker.spy(model_api.web.engine, "generate")

    body = dict(
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
        max_tokens=1,
        stop=["<", "<|"],
        temperature=0.75,
        frequency_penalty=0.75,
    )
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert spy.call_count == 1
    spy.assert_called_once_with(
        expected_prompt, expected_sampling_params, f"cmpl-{request_id}"
    )
    assert response.status_code == 200


def test_function_is_none(client, request_id, mocker):
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>person (User)
hi<|im_end|>
<|im_start|>me"""
    expected_sampling_params = SamplingParams(
        n=1,
        best_of=1,
        presence_penalty=0.0,
        frequency_penalty=0.75,
        repetition_penalty=1.0,
        temperature=0.75,
        top_p=0.99,
        top_k=-1,
        min_p=0.01,
        seed=None,
        use_beam_search=False,
        length_penalty=1.0,
        early_stopping=False,
        stop=["<", "<|"],
        stop_token_ids=[],
        include_stop_str_in_output=False,
        ignore_eos=False,
        max_tokens=1,
        logprobs=None,
        prompt_logprobs=None,
        skip_special_tokens=True,
        spaces_between_special_tokens=False,
    )

    mocker.patch("model_api.web.random_uuid", return_value=request_id)
    spy = mocker.spy(model_api.web.engine, "generate")

    body = dict(
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
        max_tokens=1,
        stop=["<", "<|"],
        temperature=0.75,
        frequency_penalty=0.75,
    )
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert spy.call_count == 1
    spy.assert_called_once_with(
        expected_prompt, expected_sampling_params, f"cmpl-{request_id}"
    )
    assert response.status_code == 200


def test_function_is_auto(client, request_id, mocker):
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
<|im_start|>person (User)
hi<|im_end|>
<|im_start|>"""
    expected_sampling_params = SamplingParams(
        n=1,
        best_of=1,
        presence_penalty=0.0,
        frequency_penalty=0.75,
        repetition_penalty=1.0,
        temperature=0.75,
        top_p=0.99,
        top_k=-1,
        min_p=0.01,
        seed=None,
        use_beam_search=False,
        length_penalty=1.0,
        early_stopping=False,
        stop=["<", "<|"],
        stop_token_ids=[],
        include_stop_str_in_output=False,
        ignore_eos=False,
        max_tokens=1,
        logprobs=None,
        prompt_logprobs=None,
        skip_special_tokens=True,
        spaces_between_special_tokens=False,
    )

    mocker.patch("model_api.web.random_uuid", return_value=request_id)
    spy = mocker.spy(model_api.web.engine, "generate")

    body = dict(
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
        max_tokens=1,
        stop=["<", "<|"],
        temperature=0.75,
        frequency_penalty=0.75,
    )
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert spy.call_count == 1
    spy.assert_called_once_with(
        expected_prompt, expected_sampling_params, f"cmpl-{request_id}"
    )
    assert response.status_code == 200


def test_rescale_temperature(client, request_id, mocker):
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>persion (User)
hi<|im_end|>
<|im_start|>me"""
    temperature = 0.7
    expected_sampling_params = SamplingParams(
        n=1,
        best_of=1,
        presence_penalty=0.0,
        frequency_penalty=0.75,
        repetition_penalty=1.0,
        temperature=0.0,
        top_p=0.99,
        top_k=-1,
        min_p=0.01,
        seed=None,
        use_beam_search=False,
        length_penalty=1.0,
        early_stopping=False,
        stop=["<", "<|"],
        stop_token_ids=[],
        include_stop_str_in_output=False,
        ignore_eos=False,
        max_tokens=1,
        logprobs=None,
        prompt_logprobs=None,
        skip_special_tokens=True,
        spaces_between_special_tokens=False,
    )

    mocker.patch("model_api.web.random_uuid", return_value=request_id)
    spy = mocker.spy(model_api.web.engine, "generate")

    body = dict(
        model=MODEL,
        temperature=temperature,
        messages=[
            {
                "role": "user",
                "name": "User",
                "content": "hi",
            }
        ],
        max_tokens=1,
        stop=["<", "<|"],    
        frequency_penalty=0.75,
    )
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert spy.call_count == 1
    spy.assert_called_once_with(
        expected_prompt, expected_sampling_params, f"cmpl-{request_id}"
    )
    assert response.status_code == 200


def test_logits_processor_fix_function_call_prediction(client, request_id, mocker):
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
<|im_start|>person (User)
hi<|im_end|>
<|im_start|>"""
    expected_sampling_params = SamplingParams(
        n=1,
        best_of=1,
        presence_penalty=0.0,
        frequency_penalty=0.75,
        repetition_penalty=1.0,
        temperature=0.75,
        top_p=0.99,
        top_k=-1,
        min_p=0.01,
        seed=None,
        use_beam_search=False,
        length_penalty=1.0,
        early_stopping=False,
        stop=["<", "<|"],
        stop_token_ids=[],
        include_stop_str_in_output=False,
        ignore_eos=False,
        max_tokens=1,
        logprobs=None,
        prompt_logprobs=None,
        skip_special_tokens=True,
        spaces_between_special_tokens=False,
        logits_processors=[fix_function_call_prediction],
    )

    mocker.patch("model_api.web.random_uuid", return_value=request_id)
    spy = mocker.spy(model_api.web.engine, "generate")

    body = dict(
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
        max_tokens=1,
        stop=["<", "<|"],
        temperature=0.75,
        frequency_penalty=0.75,
    )
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert spy.call_count == 1
    spy.assert_called_once_with(
        expected_prompt, expected_sampling_params, f"cmpl-{request_id}"
    )
    assert response.status_code == 200


def test_logits_processor_drop_disallowed_start_tags(client, request_id, mocker):
    expected_prompt = f"""<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>person (User)
hi<|im_end|>
<|im_start|>"""
    expected_sampling_params = SamplingParams(
        n=1,
        best_of=1,
        presence_penalty=0.0,
        frequency_penalty=0.75,
        repetition_penalty=1.0,
        temperature=0.75,
        top_p=0.99,
        top_k=-1,
        min_p=0.01,
        seed=None,
        use_beam_search=False,
        length_penalty=1.0,
        early_stopping=False,
        stop=["<", "<|"],
        stop_token_ids=[],
        include_stop_str_in_output=False,
        ignore_eos=False,
        max_tokens=1,
        logprobs=None,
        prompt_logprobs=None,
        skip_special_tokens=True,
        spaces_between_special_tokens=False,
        logits_processors=[drop_disallowed_start_tags]
    )

    mocker.patch("model_api.web.random_uuid", return_value=request_id)
    spy = mocker.spy(model_api.web.engine, "generate")

    body = dict(
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
        max_tokens=1,
        stop=["<", "<|"],
        temperature=0.75,
        frequency_penalty=0.75,
    )
    response = client.post(
        "/v1/chat/completions",
        json=body,
    )
    assert spy.call_count == 1
    spy.assert_called_once_with(
        expected_prompt, expected_sampling_params, f"cmpl-{request_id}"
    )
    assert response.status_code == 200
