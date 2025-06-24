from unittest.mock import MagicMock, patch

import markdown2
import markdownify
from agents_api.common.utils.evaluator import get_evaluator


def test_evaluator_csv_reader():
    """evaluator: csv reader"""
    e = get_evaluator({})
    result = e.eval('[r for r in csv.reader("a,b,c\\n1,2,3")]')
    assert result == [["a", "b", "c"], ["1", "2", "3"]]


def test_evaluator_csv_writer():
    """evaluator: csv writer"""
    e = get_evaluator({})
    result = e.eval('csv.writer("a,b,c\\n1,2,3").writerow(["4", "5", "6"])')
    assert result == 7


def test_evaluator_humanize_text_alpha():
    """evaluator: humanize_text_alpha"""
    with (
        patch("requests.post") as mock_requests_post,
        patch("litellm.completion") as mock_litellm_completion,
        patch("deep_translator.GoogleTranslator.translate") as mock_deep_translator,
    ):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"probability": 0.4}
        mock_requests_post.return_value = mock_resp
        mock_litellm_completion.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="Mock LLM Response (humanized text from LLM)"
                    )
                )
            ]
        )
        mock_deep_translator.return_value = "Mock translated text"
        evaluator = get_evaluator({})
        result = evaluator.eval('humanize_text_alpha("Hello, World!", threshold=60)')
        assert mock_requests_post.called, "Expected requests.post call"
        assert mock_litellm_completion.called, "Expected litellm.completion call"
        assert mock_deep_translator.called, "Expected GoogleTranslator.translate call"
        assert isinstance(result, str) and len(result) > 0, (
            "Expected a non-empty string response"
        )


def test_evaluator_html_to_markdown():
    """evaluator: html_to_markdown"""
    e = get_evaluator({})
    html = '<b>Yay</b> <a href="http://github.com">GitHub</a>'
    result = e.eval(f"html_to_markdown('{html}')")
    markdown = markdownify.markdownify(html)
    assert result == markdown


def test_evaluator_markdown_to_html():
    """evaluator: markdown_to_html"""
    e = get_evaluator({})
    markdown = "**Yay** [GitHub](http://github.com)"
    result = e.eval(f"markdown_to_html('{markdown}')")
    markdowner = markdown2.Markdown()
    html = markdowner.convert(markdown)
    assert result == html


def test_evaluator_safe_extract_json_basic():
    """evaluator: safe_extract_json basic"""
    e = get_evaluator({})
    result = e.eval('extract_json("""```json {"pp": "\thello"}```""")')
    assert result == {"pp": "\thello"}


def test_safe_extract_json_formats():
    """safe_extract_json with various code block formats"""
    from agents_api.common.utils.evaluator import safe_extract_json

    json_block = '```json\n    {"key": "value", "num": 123}\n    ```'
    result = safe_extract_json(json_block)
    assert result == {"key": "value", "num": 123}
    plain_block = '```\n    {"key": "value", "num": 123}\n    ```'
    result = safe_extract_json(plain_block)
    assert result == {"key": "value", "num": 123}
    plain_json = '{"key": "value", "num": 123}'
    result = safe_extract_json(plain_json)
    assert result == {"key": "value", "num": 123}
    nested_json = '```json\n    {\n        "name": "test",\n        "data": {\n            "items": [1, 2, 3],\n            "config": {"enabled": true}\n        }\n    }\n    ```'
    result = safe_extract_json(nested_json)
    assert result["name"] == "test"
    assert result["data"]["items"] == [1, 2, 3]
    assert result["data"]["config"]["enabled"] is True


def test_safe_extract_json_validation():
    """safe_extract_json handles marker validation correctly"""
    from agents_api.common.utils.evaluator import safe_extract_json

    invalid_json_marker = '``json\n    {"key": "value"}\n    ```'
    try:
        safe_extract_json(invalid_json_marker)
        assert False, "Expected ValueError was not raised"
    except ValueError as e:
        assert "Code block has invalid or missing markers" in str(e)
    invalid_plain_marker = '``\n    {"key": "value"}\n    ```'
    try:
        safe_extract_json(invalid_plain_marker)
        assert False, "Expected ValueError was not raised"
    except ValueError as e:
        assert "Code block has invalid or missing markers" in str(e)
    missing_end_marker = '```json\n    {"key": "value"}'
    try:
        safe_extract_json(missing_end_marker)
        assert False, "Expected ValueError was not raised"
    except ValueError as e:
        assert "Code block has invalid or missing markers" in str(e)
    malformed_json = '```json\n    {"key": "value", "missing": }\n    ```'
    try:
        safe_extract_json(malformed_json)
        assert False, "Expected ValueError was not raised"
    except ValueError as e:
        assert "Failed to parse JSON" in str(e)
