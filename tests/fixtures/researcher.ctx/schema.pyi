"""Schemas for the researcher fixture."""

from typing import Literal

class Finding:
    """One supported finding."""

    claim: str
    confidence: float
    sources: list[str] = []

class Input:
    """Template variables; not the reply contract — the loader ignores this."""

    persona: str
    question: str

class Output:
    """The reply contract."""

    findings: list[Finding]
    summary: str
    stance: Literal["support", "refute", "unclear"] = "unclear"
    caveats: str | None = None
