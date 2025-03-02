from unittest.mock import MagicMock, patch

import markdown2
import markdownify
from agents_api.activities.utils import get_evaluator
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
