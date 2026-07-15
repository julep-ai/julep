"""P4-2: register_pure must reject a module-top PEP 723 block instead of
silently dropping it (which fails OPEN on `import <dep>` late in the wasm tier).

`inspect.getsource(fn)` spans only the decorator-to-body range, so a block placed
above the first decorator/def is invisible. The correct, documented placement is
between `@pure(...)` and `def` -- that path must keep working.
"""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest

from julep.registry import Registry, _has_module_top_pep723_block

MODULE_TOP = textwrap.dedent(
    """\
    # /// script
    # dependencies = ["regex==2024.11.6"]
    # ///
    def extract(record):
        import regex
        return record
    """
)

BETWEEN_DECORATOR = textwrap.dedent(
    """\
    def deco(fn):
        return fn

    @deco
    # /// script
    # dependencies = ["regex==2024.11.6"]
    # ///
    def extract(record):
        import regex
        return record
    """
)

NO_BLOCK = textwrap.dedent(
    """\
    def merge(record):
        return record
    """
)

DOCSTRING_EXAMPLE = textwrap.dedent(
    '''\
    """Example module.

    Declare deps with a PEP 723 block::

        # /// script
        # dependencies = ["regex==2024.11.6"]
        # ///
    """
    def merge(record):
        return record
    '''
)
UNTERMINATED = textwrap.dedent(
    """\
    # /// script
    # dependencies = ["regex==2024.11.6"]
    def extract(record):
        import regex
        return record
    """
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (MODULE_TOP, True),
        (BETWEEN_DECORATOR, False),
        (NO_BLOCK, False),
        (DOCSTRING_EXAMPLE, False),
        (UNTERMINATED, True),
    ],
)
def test_detector_flags_only_module_top_placement(source: str, expected: bool) -> None:
    assert _has_module_top_pep723_block(source) is expected


def _load_pure_from_source(tmp_path: Path, name: str, source: str):
    """Write `source` to an importable module and return its `extract`/`merge` fn."""
    module_name = f"_p4_2_fixture_{name}"
    path = tmp_path / f"{module_name}.py"
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, "extract", None) or module.merge


def test_register_pure_rejects_module_top_block(tmp_path: Path) -> None:
    fn = _load_pure_from_source(tmp_path, "moduletop", MODULE_TOP)
    with pytest.raises(ValueError, match="module top"):
        Registry().register_pure("cad.test.moduletop.v1", fn)


def test_register_pure_accepts_between_decorator_block(tmp_path: Path) -> None:
    fn = _load_pure_from_source(tmp_path, "between", BETWEEN_DECORATOR)
    entry = Registry().register_pure("cad.test.between.v1", fn)
    assert entry.deps == ("regex==2024.11.6",)


def test_register_pure_accepts_dep_free_pure(tmp_path: Path) -> None:
    fn = _load_pure_from_source(tmp_path, "noblock", NO_BLOCK)
    entry = Registry().register_pure("cad.test.noblock.v1", fn)
    assert entry.deps == ()


def test_register_pure_accepts_pure_with_docstring_pep723_example(tmp_path: Path) -> None:
    fn = _load_pure_from_source(tmp_path, "docexample", DOCSTRING_EXAMPLE)
    entry = Registry().register_pure("cad.test.docexample.v1", fn)
    assert entry.deps == ()
