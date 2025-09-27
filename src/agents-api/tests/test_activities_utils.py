from unittest.mock import MagicMock, patch

import markdown2
import markdownify
from agents_api.common.utils.evaluator import get_evaluator
from ward import test


@test("evaluator: csv reader")
def _():
    e = get_evaluator({})
    result = e.eval('[r for r in csv.reader("a,b,c\\n1,2,3")]')
    assert result == [["a", "b", "c"], ["1", "2", "3"]]


@test("evaluator: csv writer")
def _():
    e = get_evaluator({})
    result = e.eval('csv.writer("a,b,c\\n1,2,3").writerow(["4", "5", "6"])')
    # at least no exceptions
    assert result == 7


@test("evaluator: humanize_text_alpha")
def _():
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
                    message=MagicMock(content="Mock LLM Response (humanized text from LLM)"),
                ),
            ],
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


@test("evaluator: html_to_markdown")
def _():
    e = get_evaluator({})
    html = '<b>Yay</b> <a href="http://github.com">GitHub</a>'
    result = e.eval(f"""html_to_markdown('{html}')""")
    markdown = markdownify.markdownify(html)
    assert result == markdown


@test("evaluator: markdown_to_html")
def _():
    e = get_evaluator({})
    markdown = "**Yay** [GitHub](http://github.com)"
    result = e.eval(f"""markdown_to_html('{markdown}')""")
    markdowner = markdown2.Markdown()
    html = markdowner.convert(markdown)
    assert result == html


@test("evaluator: safe_extract_json basic")
def _():
    e = get_evaluator({})
    result = e.eval('extract_json("""```json {"pp": "\thello"}```""")')
    assert result == {"pp": "\thello"}


@test("safe_extract_json with various code block formats")
def test_safe_extract_json_formats():
    from agents_api.common.utils.evaluator import safe_extract_json

    # Test with ```json format
    json_block = """```json
    {"key": "value", "num": 123}
    ```"""
    result = safe_extract_json(json_block)
    assert result == {"key": "value", "num": 123}

    # Test with plain ``` format containing JSON
    plain_block = """```
    {"key": "value", "num": 123}
    ```"""
    result = safe_extract_json(plain_block)
    assert result == {"key": "value", "num": 123}

    # Test with no code block, just JSON
    plain_json = """{"key": "value", "num": 123}"""
    result = safe_extract_json(plain_json)
    assert result == {"key": "value", "num": 123}

    # Test with nested JSON structure
    nested_json = """```json
    {
        "name": "test",
        "data": {
            "items": [1, 2, 3],
            "config": {"enabled": true}
        }
    }
    ```"""
    result = safe_extract_json(nested_json)
    assert result["name"] == "test"
    assert result["data"]["items"] == [1, 2, 3]
    assert result["data"]["config"]["enabled"] is True


@test("safe_extract_json handles marker validation correctly")
def test_safe_extract_json_validation():
    from agents_api.common.utils.evaluator import safe_extract_json

    # Test invalid start marker validation for ```json format
    invalid_json_marker = """``json
    {"key": "value"}
    ```"""
    try:
        safe_extract_json(invalid_json_marker)
        assert False, "Expected ValueError was not raised"
    except ValueError as e:
        assert "Code block has invalid or missing markers" in str(e)

    # Test invalid start marker validation for plain ``` format
    invalid_plain_marker = """``
    {"key": "value"}
    ```"""
    try:
        safe_extract_json(invalid_plain_marker)
        assert False, "Expected ValueError was not raised"
    except ValueError as e:
        assert "Code block has invalid or missing markers" in str(e)

    # Test missing end marker validation
    missing_end_marker = """```json
    {"key": "value"}"""
    try:
        safe_extract_json(missing_end_marker)
        assert False, "Expected ValueError was not raised"
    except ValueError as e:
        assert "Code block has invalid or missing markers" in str(e)

    # Test with malformed JSON
    malformed_json = """```json
    {"key": "value", "missing": }
    ```"""
    try:
        safe_extract_json(malformed_json)
        assert False, "Expected ValueError was not raised"
    except ValueError as e:
        assert "Failed to parse JSON" in str(e)
