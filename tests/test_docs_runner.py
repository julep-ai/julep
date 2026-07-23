from pathlib import Path

from tests._docs_runner import extract_blocks


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "doc.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_extracts_plain_python_block(tmp_path: Path) -> None:
    doc = _write(tmp_path, "intro\n\n```python\nprint(1)\n```\n\nmore\n")
    blocks = extract_blocks(doc)
    assert len(blocks) == 1
    assert blocks[0].lang == "python"
    assert blocks[0].code == "print(1)\n"
    assert blocks[0].directive is None
    assert blocks[0].expected_output is None


def test_skip_directive(tmp_path: Path) -> None:
    doc = _write(tmp_path, "<!-- julep:doctest skip -->\n```python\nbad(\n```\n")
    assert extract_blocks(doc)[0].directive == "skip"


def test_expect_output_captures_following_text_block(tmp_path: Path) -> None:
    doc = _write(
        tmp_path,
        "<!-- julep:doctest expect-output -->\n```python\nprint('Dataflow')\n```\n\n```text\nDataflow\n```\n",
    )
    b = extract_blocks(doc)[0]
    assert b.directive == "expect-output"
    assert b.expected_output == "Dataflow\n"


def test_raises_directive(tmp_path: Path) -> None:
    doc = _write(
        tmp_path,
        "<!-- julep:doctest raises=DefineError -->\n```python\nboom()\n```\n",
    )
    assert extract_blocks(doc)[0].directive == "raises=DefineError"
