"""Minimal local-directory content-addressed store for the P1(b) spike."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


class CasIntegrityError(RuntimeError):
    """Raised when stored bytes do not match their requested digest."""


class LocalDirCas:
    """Write-once sha256-addressed blob store over a local directory."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, data: bytes) -> str:
        digest = hashlib.sha256(data).hexdigest()
        path = self._path_for(digest)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            stored = path.read_bytes()
            if hashlib.sha256(stored).hexdigest() != digest or stored != data:
                raise CasIntegrityError(f"CAS collision or corruption for {digest}")
            return digest
        path.write_bytes(data)
        return digest

    def get(self, digest: str) -> bytes:
        path = self._path_for(digest)
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != digest:
            raise CasIntegrityError(f"CAS corruption for {digest}: read {actual}")
        return data

    def _path_for(self, digest: str) -> Path:
        if _SHA256_HEX.fullmatch(digest) is None:
            raise ValueError(f"expected full sha256 hex digest, got {digest!r}")
        return self.root / digest[:2] / digest[2:4] / digest
