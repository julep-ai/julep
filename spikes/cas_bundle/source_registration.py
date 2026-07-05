"""Spike-only helpers for registering bundled pures from shipped source text."""

from __future__ import annotations

import linecache
import hashlib
import sys
from types import ModuleType

from julep import pure
from julep.purity import source_hash_of


def registry_text_hash(source: str) -> str:
    return f"pure:{hashlib.sha256(source.encode('utf-8')).hexdigest()[:16]}"


def assert_authoring_flow_not_loaded() -> None:
    loaded = sorted(name for name in sys.modules if name.endswith("authoring_flow"))
    if loaded:
        raise RuntimeError(f"worker imported authoring flow module(s): {loaded}")


def register_pure_source_linecache(name: str, source: str) -> str:
    """Exec shipped decorated source so inspect.getsource hashes the shipped text.

    The existing @pure decorator calls Registry.register_pure during exec. We
    populate linecache before exec so registry.py _source_hash can recover exactly
    this source text instead of falling back to module.qualname.
    """

    expected = registry_text_hash(source)
    filename = f"<cas-bundle-pure:{name}:{expected}>"
    source_with_newline = source if source.endswith("\n") else f"{source}\n"
    linecache.cache[filename] = (
        len(source_with_newline),
        None,
        source_with_newline.splitlines(keepends=True),
        filename,
    )

    module = ModuleType(f"_cas_bundle_pure_{name.replace('.', '_')}")
    module.__dict__["__file__"] = filename
    module.__dict__["pure"] = pure
    code = compile(source_with_newline, filename, "exec")
    exec(code, module.__dict__)

    actual = source_hash_of(name)
    if actual != expected:
        raise RuntimeError(f"registered pure hash mismatch for {name}: {actual} != {expected}")
    return actual
