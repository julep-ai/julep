from __future__ import annotations

import pytest

from julep._specload import resolve_spec
from julep.execution.serve import load_context_factory


def test_resolve_spec_resolves_dotted_callable() -> None:
    resolved = resolve_spec("pathlib:Path.cwd", what="loader")
    assert resolved is not None
    assert callable(resolved)
    delegated = load_context_factory("pathlib:Path.cwd")
    assert delegated.__func__ is resolved.__func__


@pytest.mark.parametrize(
    ("spec", "message"),
    [
        ("pathlib", "module:attr"),
        ("no_such_julep_test_module:value", "cannot import"),
        ("pathlib:Path.no_such_attr", "no attribute"),
        ("pathlib:Path.__module__", "not callable"),
    ],
)
def test_resolve_spec_errors_include_shape_and_noun(spec: str, message: str) -> None:
    with pytest.raises(ValueError) as caught:
        resolve_spec(spec, what="test caller")
    assert message in str(caught.value)
    assert "test caller" in str(caught.value)
    if message != "cannot import":
        assert spec in str(caught.value)
