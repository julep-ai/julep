"""Schemas for the issue-dedup planner."""

from typing import Literal


class Input:
    """Template variables for prompt.j2 (documentation only; the loader ignores this)."""

    issue: str
    category: str
    thread_id: str | None = None


class Output:
    """The planner's structured decision (the reply contract).

    Conditional requirements from the source model (create needs a title;
    comment/upvote need matched_post_id) are a consumer-side validation concern and
    are not expressed in this structural JSON Schema.
    """

    action: Literal["create", "comment", "upvote"]
    matched_post_id: str | None = None
    title: str | None = None
    comment: str | None = None
    reason: str
