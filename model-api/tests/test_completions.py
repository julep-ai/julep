# ruff: noqa: F401, F811
from pytest_mock import mocker
from vllm.sampling_params import SamplingParams

import model_api.web
from model_api.logits_processors import drop_disallowed_start_tags
from tests.fixtures import client, unauthorized_client, request_id, MODEL


def test_security(unauthorized_client):
    response = unauthorized_client.post("/v1/completions")
    assert response.status_code == 403


def test_check_model(client):
    body = dict(
        model="some_nonexistent_model",
        prompt="some text",
    )
    response = client.post(
        "/v1/completions",
        json=body,
    )
    assert response.status_code == 404


def test_logit_bias_not_supported(client):
    body = dict(
        model=MODEL,
        logit_bias={"a": 1.0},
        prompt="some text",
    )
    response = client.post(
        "/v1/completions",
        json=body,
    )
    assert response.status_code == 400


def test_remove_last_space(client, request_id, mocker):
    expected_prompt = """<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>person (User)
hi<|im_end|>
<|im_start|>me  """
    prompt = expected_prompt
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
        prompt=prompt,
        max_tokens=1,
        stop=["<", "<|"],
        temperature=0.75,
        frequency_penalty=0.75,
    )
    response = client.post(
        "/v1/completions",
        json=body,
    )
    assert spy.call_count == 1
    spy.assert_called_once_with(
        expected_prompt, expected_sampling_params, f"cmpl-{request_id}"
    )
    assert response.status_code == 200


def test_remove_last_space_2(client, request_id, mocker):
    st = list(
        model_api.web.engine.engine.tokenizer.tokenizer.special_tokens_map.values()
    )[0]
    if isinstance(st, list):
        st = st[0]
    expected_prompt = """<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>person (User)
hi<|im_end|>
<|im_start|>me"""
    prompt = expected_prompt + " "
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
        prompt=prompt,
        max_tokens=1,
        stop=["<", "<|"],
        temperature=0.75,
        frequency_penalty=0.75,
    )
    response = client.post(
        "/v1/completions",
        json=body,
    )
    assert spy.call_count == 1
    spy.assert_called_once_with(
        expected_prompt, expected_sampling_params, f"cmpl-{request_id}"
    )
    assert response.status_code == 200


# def test_rescale_temperature(client, request_id, mocker):
#     expected_prompt = f"""<|im_start|>situation
# You are a helpful AI Assistant<|im_end|>
# <|im_start|>person (User)
# hi<|im_end|>
# <|im_start|>me
# """
#     prompt = expected_prompt
#     temperature = 0.7
#     expected_sampling_params = SamplingParams(
#         n=1,
#         best_of=1,
#         presence_penalty=0.0,
#         frequency_penalty=0.75,
#         repetition_penalty=1.0,
#         temperature=0.0,
#         top_p=0.99,
#         top_k=-1,
#         min_p=0.01,
#         seed=None,
#         use_beam_search=False,
#         length_penalty=1.0,
#         early_stopping=False,
#         stop=["<", "<|"],
#         stop_token_ids=[],
#         include_stop_str_in_output=False,
#         ignore_eos=False,
#         max_tokens=1,
#         logprobs=None,
#         prompt_logprobs=None,
#         skip_special_tokens=True,
#         spaces_between_special_tokens=False,
#     )

#     mocker.patch("model_api.web.random_uuid", return_value=request_id)
#     spy = mocker.spy(model_api.web.engine, "generate")

#     body = dict(
#         model=MODEL,
#         temperature=temperature,
#         prompt=prompt,
#         max_tokens=1,
#         stop=["<", "<|"],
#         frequency_penalty=0.75,
#     )
#     response = client.post(
#         "/v1/completions",
#         json=body,
#     )
#     assert spy.call_count == 1
#     spy.assert_called_once_with(
#         expected_prompt, expected_sampling_params, f"cmpl-{request_id}"
#     )
#     assert response.status_code == 200


def test_logits_processor_drop_disallowed_start_tags(client, request_id, mocker):
    expected_prompt = """<|im_start|>situation
You are a helpful AI Assistant<|im_end|>
<|im_start|>person (User)
hi<|im_end|>
<|im_start|>"""
    prompt = expected_prompt
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
        logits_processors=[drop_disallowed_start_tags],
    )

    mocker.patch("model_api.web.random_uuid", return_value=request_id)
    spy = mocker.spy(model_api.web.engine, "generate")

    body = dict(
        model=MODEL,
        prompt=prompt,
        max_tokens=1,
        stop=["<", "<|"],
        temperature=0.75,
        frequency_penalty=0.75,
    )
    response = client.post(
        "/v1/completions",
        json=body,
    )
    assert spy.call_count == 1
    spy.assert_called_once_with(
        expected_prompt, expected_sampling_params, f"cmpl-{request_id}"
    )
    assert response.status_code == 200
